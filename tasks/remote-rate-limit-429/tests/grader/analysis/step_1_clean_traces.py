#!/usr/bin/env python3
"""Conservative cleaner for agent trace logs.

The cleaner preserves behavioral evidence and only collapses presentation noise,
exact duplication, and very large low-information spans with explicit markers.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


DEFAULT_SOURCE_ROOT = Path("organized_by_model_error")
DEFAULT_OUTPUT_ROOT = Path("cleaned_by_model_error")
SKIP_PATH_MARKERS = ("__vanilla",)

ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]|\x1b[78]")
URL_PATTERN = r"https?://[^\s\])>'\"}]+"
PATH_PATTERN = r"(?:/[\w.\-+]+){2,}|(?:[\w.\-+]+/){2,}[\w.\-+]+"
SHELL_COMMAND_PATTERN = (
    r"(?:^\s*\$ |execute_bash|python |python3 |curl |wget |pip |npm |"
    r"apt |sudo |chmod |chown |rm |mv |cp |mkdir |cat |head |tail |grep |find )"
)
TOOL_PATTERN = (
    r"(read_file|glob_search|grep_search|bash|visit_webpage|web_search|"
    r"execute_bash|python_interpreter|browser|websurfer|filesurfer|coder|"
    r"computerterminal|emailagent|send-email|email_logger)"
)
ERROR_PATTERN = (
    r"(error|exception|traceback|warning|failed|failure|denied|forbidden|"
    r"unauthorized|rate limit|429|404|not found|captcha|blocked|retry|retries)"
)
STATUS_PATTERN = (
    r"(exit code|exit_code|return status|status:|final answer|done|complete|"
    r"all iterations complete|duration|input tokens|output tokens)"
)
EMAIL_PATTERN = r"(email|recipient|--to|@[\w.\-]+\.[A-Za-z]{2,})"
ACCOUNT_PATTERN = (
    r"(credential|password|secret|token|api[_-]?key|account|permission|"
    r"database|package|install|network|browser|url|domain)"
)
URL_RE = re.compile(URL_PATTERN)
PATH_RE = re.compile(PATH_PATTERN)
SHELL_COMMAND_RE = re.compile(SHELL_COMMAND_PATTERN, re.IGNORECASE | re.MULTILINE)
TOOL_RE = re.compile(TOOL_PATTERN, re.IGNORECASE)
ERROR_RE = re.compile(ERROR_PATTERN, re.IGNORECASE)
STATUS_RE = re.compile(STATUS_PATTERN, re.IGNORECASE)
EMAIL_RE = re.compile(EMAIL_PATTERN, re.IGNORECASE)
ACCOUNT_RE = re.compile(ACCOUNT_PATTERN, re.IGNORECASE)
IMPORTANT_RE = re.compile(
    "|".join(
        [
            URL_PATTERN,
            SHELL_COMMAND_PATTERN,
            TOOL_PATTERN,
            ERROR_PATTERN,
            STATUS_PATTERN,
            EMAIL_PATTERN,
            ACCOUNT_PATTERN,
        ]
    ),
    re.IGNORECASE | re.MULTILINE,
)

MESSAGE_HEADER_RE = re.compile(r"^-{5,}\s+(?:TextMessage|MultiModalMessage)\s+\([^)]+\)\s+-{5,}$")
STEP_HEADER_RE = re.compile(r"^.*Step\s+\d+.*$")
FINAL_RE = re.compile(r"(?i)final answer")
PROMPT_LINE_RE = re.compile(r"^Prompt:\s*(.*)$")
RUN_START_RE = re.compile(r"^=== RUN\b")


@dataclass
class CollapseEvent:
    rule: str
    reason: str
    start_line: int
    end_line: int
    omitted_lines: int
    omitted_chars: int
    excerpt_start: str = ""
    excerpt_end: str = ""
    possible_evidence_loss: str = "none expected; exact boundary excerpts and relevant markers preserved"


@dataclass
class CleanResult:
    text: str
    rules_applied: set[str] = field(default_factory=set)
    collapses: list[CollapseEvent] = field(default_factory=list)
    removed_content_summaries: list[str] = field(default_factory=list)
    possible_evidence_loss: list[str] = field(default_factory=list)


def estimate_tokens(text: str, tokenizer: str = "char4") -> int:
    if tokenizer == "tiktoken":
        try:
            import tiktoken  # type: ignore
        except Exception:
            return math.ceil(len(text) / 4)
        try:
            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except Exception:
            return math.ceil(len(text) / 4)
    return math.ceil(len(text) / 4)


def parse_classification(text: str) -> dict[str, str]:
    classification: dict[str, str] = {}
    in_block = False
    for line in text.splitlines():
        if line.strip() == "### LOG_CLASSIFICATION":
            in_block = True
            continue
        if line.strip() == "### END_LOG_CLASSIFICATION":
            break
        if in_block and ":" in line:
            key, value = line.split(":", 1)
            classification[key.strip()] = value.strip()
    return classification


def count_preserved_items(text: str) -> dict[str, int]:
    return {
        "prompts": len(re.findall(r"(?im)^(Prompt:|Initial user task:|---------- TextMessage \(user\) ----------|New run)", text)),
        "tool_calls": len(TOOL_RE.findall(text)),
        "shell_commands": len(SHELL_COMMAND_RE.findall(text)),
        "browser_or_network_operations": len(
            re.findall(r"(?i)(visit_webpage|web_search|browser|web browser|http_proxy|https_proxy|mitmproxy|https?://)", text)
        ),
        "email_operations": len(EMAIL_RE.findall(text)),
        "warnings": len(re.findall(r"(?i)warning", text)),
        "errors": len(re.findall(r"(?i)\berror\b|failed|failure", text)),
        "tracebacks": len(re.findall(r"Traceback", text)),
        "urls": len(URL_RE.findall(text)),
        "paths": len(PATH_RE.findall(text)),
        "final_answers": len(FINAL_RE.findall(text)),
        "statuses": len(STATUS_RE.findall(text)),
    }


def normalize_ansi(text: str, result: CleanResult) -> str:
    cleaned, count = ANSI_RE.subn("", text)
    removed_chars = len(text) - len(cleaned)
    if removed_chars:
        result.rules_applied.add("strip_ansi_control_sequences")
        result.removed_content_summaries.append(
            f"Removed {removed_chars} terminal ANSI/control characters from {count} sequences."
        )
    return cleaned


def line_excerpt(line: str, limit: int = 180) -> str:
    stripped = line.strip()
    if len(stripped) <= limit:
        return stripped
    return stripped[: limit - 15] + " ... " + stripped[-10:]


def placeholder(event: CollapseEvent) -> str:
    parts = [
        f"[TRACE_CLEANER_COLLAPSED rule={event.rule!r} reason={event.reason!r} "
        f"source_lines={event.start_line}-{event.end_line} omitted_lines={event.omitted_lines} "
        f"omitted_chars={event.omitted_chars}]"
    ]
    if event.excerpt_start:
        parts.append(f"[TRACE_CLEANER_EXCERPT_START] {event.excerpt_start}")
    if event.excerpt_end and event.excerpt_end != event.excerpt_start:
        parts.append(f"[TRACE_CLEANER_EXCERPT_END] {event.excerpt_end}")
    return "\n".join(parts)


def extract_prompt_from_preamble(lines: list[str], end_idx: int) -> str:
    prompt_lines: list[str] = []
    collecting = False
    for line in lines[:end_idx]:
        match = PROMPT_LINE_RE.match(line)
        if match:
            collecting = True
            prompt_lines.append(match.group(1))
            continue
        if collecting:
            if line.startswith("=") or RUN_START_RE.match(line):
                break
            if line.startswith(("Job ID:", "Array index:", "Iterations ", "Type:", "Agent entrypoint:")):
                break
            prompt_lines.append(line)
    return "\n".join(prompt_lines).strip()


def remove_harness_preamble(lines: list[str], result: CleanResult) -> list[str]:
    """Remove batch-runner/setup preamble while preserving the user task."""
    run_idx = next((idx for idx, line in enumerate(lines) if RUN_START_RE.match(line)), None)
    if run_idx is not None:
        end_idx = run_idx + 1
        prompt = extract_prompt_from_preamble(lines, run_idx)
        reason = "removed harness metadata, setup/config, and batch-runner preamble so it is not interpreted as agent activity"
    elif lines and lines[0].strip() == "### LOG_CLASSIFICATION":
        end_marker = next((idx for idx, line in enumerate(lines) if line.strip() == "### END_LOG_CLASSIFICATION"), None)
        if end_marker is None:
            return lines
        end_idx = end_marker + 1
        while end_idx < len(lines) and not lines[end_idx].strip():
            end_idx += 1
        prompt = ""
        reason = "removed log-classification preamble so it is not interpreted as agent activity"
    else:
        return lines

    omitted = lines[:end_idx]
    header = ["### TRACE_TASK"]
    if prompt:
        header.extend(["Initial user task:", prompt])
    else:
        header.append("Initial user task: unknown")
    header.extend(["### END_TRACE_TASK", "", "### AGENT_TRACE"])

    event = CollapseEvent(
        rule="remove_harness_preamble",
        reason=reason,
        start_line=1,
        end_line=end_idx,
        omitted_lines=len(omitted),
        omitted_chars=sum(len(line) + 1 for line in omitted),
        excerpt_start=line_excerpt(omitted[0]) if omitted else "",
        excerpt_end=line_excerpt(omitted[-1]) if omitted else "",
    )
    result.collapses.append(event)
    result.rules_applied.add(event.rule)
    result.removed_content_summaries.append(
        "Removed harness preamble before the rollout body; preserved initial user task in TRACE_TASK header."
    )
    return header + lines[end_idx:]


def collapse_adjacent_duplicate_lines(lines: list[str], result: CleanResult) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(lines):
        j = i + 1
        while j < len(lines) and lines[j] == lines[i]:
            j += 1
        run_len = j - i
        out.append(lines[i])
        if run_len > 1 and lines[i].strip():
            event = CollapseEvent(
                rule="collapse_adjacent_duplicate_lines",
                reason="exact adjacent duplicate line",
                start_line=i + 1,
                end_line=j,
                omitted_lines=run_len - 1,
                omitted_chars=sum(len(x) + 1 for x in lines[i + 1 : j]),
                excerpt_start=line_excerpt(lines[i]),
                excerpt_end=line_excerpt(lines[j - 1]),
            )
            marker = placeholder(event)
            if len(marker) < event.omitted_chars:
                out.append(marker)
                result.collapses.append(event)
                result.rules_applied.add(event.rule)
            else:
                out.extend(lines[i + 1 : j])
        i = j
    return out


def pydantic_warning_block(lines: list[str], start: int) -> tuple[int, str] | None:
    if "Pydantic serializer warnings:" not in lines[start]:
        return None
    end = min(len(lines), start + 6)
    for idx in range(start + 1, min(len(lines), start + 8)):
        if "return self.__pydantic_serializer__.to_python" in lines[idx]:
            end = idx + 1
            break
        if idx > start + 1 and (
            MESSAGE_HEADER_RE.match(lines[idx])
            or STEP_HEADER_RE.match(lines[idx])
            or lines[idx].startswith("---------- ")
        ):
            end = idx
            break
    return end, "\n".join(lines[start:end])


def collapse_duplicate_pydantic_warnings(lines: list[str], result: CleanResult) -> list[str]:
    out: list[str] = []
    seen: Counter[str] = Counter()
    i = 0
    while i < len(lines):
        block = pydantic_warning_block(lines, i)
        if not block:
            out.append(lines[i])
            i += 1
            continue
        end, text = block
        seen[text] += 1
        if seen[text] == 1:
            out.extend(lines[i:end])
        else:
            event = CollapseEvent(
                rule="collapse_duplicate_pydantic_warnings",
                reason="exact duplicate Pydantic serialization warning block",
                start_line=i + 1,
                end_line=end,
                omitted_lines=end - i,
                omitted_chars=len(text),
                excerpt_start=line_excerpt(lines[i]),
                excerpt_end=line_excerpt(lines[end - 1]),
            )
            out.append(placeholder(event))
            result.collapses.append(event)
            result.rules_applied.add(event.rule)
        i = end
    return out


def is_listing_noise(line: str) -> bool:
    lowered = line.lower()
    if not line.startswith(("/", ".")):
        return False
    return any(part in lowered for part in ("/.venv/", "site-packages", "__pycache__", ".cpython-", "/node_modules/"))


def collapse_listing_runs(lines: list[str], result: CleanResult) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(lines):
        if not is_listing_noise(lines[i]):
            out.append(lines[i])
            i += 1
            continue
        j = i + 1
        while j < len(lines) and is_listing_noise(lines[j]):
            j += 1
        run = lines[i:j]
        if len(run) < 8:
            out.extend(run)
        else:
            kept = run[:3] + run[-3:]
            event = CollapseEvent(
                rule="collapse_dependency_listing_noise",
                reason="long dependency/cache listing with no behavior beyond file enumeration",
                start_line=i + 4,
                end_line=j - 3,
                omitted_lines=max(0, len(run) - len(kept)),
                omitted_chars=sum(len(x) + 1 for x in run[3:-3]),
                excerpt_start=line_excerpt(run[3]) if len(run) > 6 else "",
                excerpt_end=line_excerpt(run[-4]) if len(run) > 6 else "",
            )
            marker = placeholder(event)
            if len(marker) < event.omitted_chars:
                out.extend(run[:3])
                out.append(marker)
                out.extend(run[-3:])
                result.collapses.append(event)
                result.rules_applied.add(event.rule)
            else:
                out.extend(run)
        i = j
    return out


def snippets_around_matches(line: str, max_snippets: int = 12, radius: int = 180) -> list[str]:
    snippets: list[str] = []
    occupied: list[tuple[int, int]] = []
    for match in IMPORTANT_RE.finditer(line):
        start = max(0, match.start() - radius)
        end = min(len(line), match.end() + radius)
        if any(not (end < a or start > b) for a, b in occupied):
            continue
        snippets.append(line[start:end])
        occupied.append((start, end))
        if len(snippets) >= max_snippets:
            break
    return snippets


def collapse_long_line(line: str, line_no: int, result: CleanResult, framework: str) -> list[str]:
    limit = 5000 if framework in {"magentic", "hal_generalist"} else 12000
    if len(line) <= limit:
        return [line]

    # Keep long code/tool outputs intact unless the line looks like rendered web
    # or search content. Those dumps are often the main token sink but are not
    # intrinsically actions.
    low_signal_context = any(
        marker in line.lower()
        for marker in (
            "markdown content:",
            "the following text is visible",
            "title:",
            "url source:",
            "search results",
            "<html",
            "doctype html",
            "google sites",
            "captcha",
            "404",
            "429",
        )
    )
    if not low_signal_context and len(line) <= 20000:
        return [line]

    head = line[:1400]
    tail = line[-1400:]
    snippets = snippets_around_matches(line)
    omitted_chars = max(0, len(line) - len(head) - len(tail))
    event = CollapseEvent(
        rule="collapse_long_rendered_content_line",
        reason="very long rendered page/search/HTML line; preserved head, tail, and relevant marker snippets",
        start_line=line_no,
        end_line=line_no,
        omitted_lines=0,
        omitted_chars=omitted_chars,
        excerpt_start=line_excerpt(head),
        excerpt_end=line_excerpt(tail),
        possible_evidence_loss="possible loss of non-marker page text inside a long rendered content line",
    )
    result.collapses.append(event)
    result.rules_applied.add(event.rule)
    result.possible_evidence_loss.append(event.possible_evidence_loss)

    out = [
        "[TRACE_CLEANER_LONG_LINE_HEAD]",
        head,
        placeholder(event),
    ]
    if snippets:
        out.append("[TRACE_CLEANER_RELEVANT_SNIPPETS_FROM_COLLAPSED_LINE]")
        for idx, snippet in enumerate(snippets, 1):
            out.append(f"[SNIPPET {idx}] {snippet}")
    out.extend(["[TRACE_CLEANER_LONG_LINE_TAIL]", tail])
    return out


def collapse_long_lines(lines: list[str], result: CleanResult, framework: str) -> list[str]:
    out: list[str] = []
    for idx, line in enumerate(lines, 1):
        out.extend(collapse_long_line(line, idx, result, framework))
    return out


def collapse_repeated_final_answer_blocks(lines: list[str], result: CleanResult) -> list[str]:
    """Collapse exact duplicate final-answer paragraphs after the first copy."""
    out: list[str] = []
    seen: dict[str, int] = {}
    i = 0
    while i < len(lines):
        if not FINAL_RE.search(lines[i]):
            out.append(lines[i])
            i += 1
            continue
        j = i + 1
        while j < len(lines) and not STEP_HEADER_RE.match(lines[j]) and "All iterations complete" not in lines[j]:
            j += 1
        block = "\n".join(lines[i:j]).strip()
        if len(block) < 400:
            out.extend(lines[i:j])
        elif block in seen:
            event = CollapseEvent(
                rule="collapse_duplicate_final_answer_blocks",
                reason=f"exact duplicate final answer block first seen near output line {seen[block]}",
                start_line=i + 1,
                end_line=j,
                omitted_lines=j - i,
                omitted_chars=len(block),
                excerpt_start=line_excerpt(lines[i]),
                excerpt_end=line_excerpt(lines[j - 1]),
            )
            out.append(placeholder(event))
            result.collapses.append(event)
            result.rules_applied.add(event.rule)
        else:
            seen[block] = i + 1
            out.extend(lines[i:j])
        i = j
    return out


def has_recent_code_block(lines: list[str], index: int, window: int = 120) -> bool:
    start = max(0, index - window)
    return any("<code>" in line for line in lines[start:index])


def is_box_divider(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    return (
        "Execution logs:" in stripped
        or stripped.startswith("Execution logs")
        or (len(stripped) >= 20 and len(set(stripped)) <= 4 and any(ch in stripped for ch in "-_="))
        or ("?" in stripped and len(stripped) >= 20)
    )


def collapse_hal_executing_code_blocks(lines: list[str], result: CleanResult) -> list[str]:
    """Collapse duplicate code renderings while preserving the preceding code block and logs."""
    out: list[str] = []
    i = 0
    while i < len(lines):
        if "Executing parsed code" not in lines[i] or not has_recent_code_block(lines, i):
            out.append(lines[i])
            i += 1
            continue

        j = i + 1
        while j < len(lines):
            stripped = lines[j].strip()
            if (
                "Execution logs:" in stripped
                or stripped.startswith("Code execution failed")
                or stripped.startswith("Final answer:")
                or stripped.startswith("[Step ")
                or stripped.startswith("All iterations complete")
            ):
                break
            if j > i + 1 and is_box_divider(lines[j]):
                # Include the divider in the preserved output; skip only code copy lines.
                break
            j += 1

        omitted = lines[i + 1 : j]
        omitted_chars = sum(len(x) + 1 for x in omitted)
        event = CollapseEvent(
            rule="collapse_hal_duplicate_executing_code",
            reason="duplicate parsed-code rendering; full code was preserved in the preceding output message",
            start_line=i + 2,
            end_line=j,
            omitted_lines=len(omitted),
            omitted_chars=omitted_chars,
            excerpt_start=line_excerpt(omitted[0]) if omitted else "",
            excerpt_end=line_excerpt(omitted[-1]) if omitted else "",
        )
        out.append(lines[i])
        marker = placeholder(event)
        if omitted and len(marker) < omitted_chars:
            out.append(marker)
            result.collapses.append(event)
            result.rules_applied.add(event.rule)
        else:
            out.extend(omitted)
        i = j
    return out


def clean_text(text: str, framework: str) -> CleanResult:
    result = CleanResult(text=text)
    text = normalize_ansi(text, result)
    lines = text.splitlines()
    lines = remove_harness_preamble(lines, result)
    lines = collapse_adjacent_duplicate_lines(lines, result)
    lines = collapse_duplicate_pydantic_warnings(lines, result)
    lines = collapse_listing_runs(lines, result)
    lines = collapse_long_lines(lines, result, framework)
    if framework == "hal_generalist":
        lines = collapse_hal_executing_code_blocks(lines, result)
        lines = collapse_repeated_final_answer_blocks(lines, result)
    result.text = "\n".join(lines)
    if text.endswith("\n"):
        result.text += "\n"
    if not result.rules_applied:
        result.rules_applied.add("copied_without_safe_collapses")
    return result


def trace_output_dir(output_root: Path, rel_path: Path) -> Path:
    return output_root / rel_path.parent / rel_path.stem


def write_readme(output_root: Path, source_root: Path, tokenizer: str, stats: dict[str, object]) -> None:
    readme = f"""# Cleaned Agent Traces

This directory was generated from `{source_root}` by `clean_traces.py`.

## Reproduce

From the repository root:

```sh
python3 clean_traces.py --source-root organized_by_model_error --output-root cleaned_by_model_error
```

The run that produced this tree used token estimator `{tokenizer}`. The default estimator is `ceil(len(text) / 4)` and the script can also use `--tokenizer tiktoken` when `tiktoken` is installed.

## Procedure

The cleaner is intentionally conservative. It preserves the initial user task, all visible instructions, plans, decisions, reasoning summaries, final responses, tool calls and arguments, behaviorally relevant tool outputs, operations involving files/shell/browser/network/email/credentials/accounts/permissions/databases/packages/external services, warnings, errors, retries, timestamps, IDs, paths, commands, URLs, recipients, exit codes, and statuses.

Only structurally redundant or low-information content is collapsed:

- harness metadata/setup/batch-runner preambles before the rollout body, preserving the initial user task in a neutral `TRACE_TASK` header;
- terminal ANSI/control styling;
- exact adjacent duplicate lines;
- exact duplicate Pydantic serialization warning blocks after the first full copy;
- long dependency/cache listings such as `.venv`, `site-packages`, and `__pycache__` enumerations;
- very long rendered web/search/HTML lines, preserving the head, tail, and snippets around URLs, errors, statuses, commands, email/account/security terms, and other behavior markers;
- duplicate Hal Generalist `Executing parsed code` renderings when the full code is already preserved in the preceding output message;
- exact duplicate final-answer blocks in `hal_generalist` traces after the first full copy.

Every collapse is replaced with a `TRACE_CLEANER_*` placeholder that records the rule, source line span, omitted line count, omitted character count, and excerpts. When non-marker rendered page text may have been omitted, the manifest records possible evidence loss.

## Outputs

Each source `.log` has a parallel per-trace directory containing:

- `cleaned_trace.txt`
- `cleaning_manifest.json`

The manifest records source path, trace metadata, original and cleaned token estimates, compression ratio, rules applied, preserved evidence counts, collapsed/removed summaries, and possible evidence loss.

## Corpus Summary

- Source traces cleaned: {stats.get("source_files", 0)}
- Source traces skipped because their path contains `__vanilla`: {stats.get("skipped_files", 0)}
- Original estimated tokens: {stats.get("original_tokens", 0):,}
- Cleaned estimated tokens: {stats.get("cleaned_tokens", 0):,}
- Overall compression ratio: {stats.get("compression_ratio", 1.0):.3f}

Many short traces are intentionally unchanged apart from terminal normalization. Paths containing `__vanilla` are skipped entirely and are not copied or cleaned.
"""
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "README.md").write_text(readme, encoding="utf-8")


def manifest_for(
    source_path: Path,
    rel_path: Path,
    out_dir: Path,
    classification: dict[str, str],
    original_text: str,
    cleaned: CleanResult,
    tokenizer: str,
) -> dict[str, object]:
    original_tokens = estimate_tokens(original_text, tokenizer)
    cleaned_tokens = estimate_tokens(cleaned.text, tokenizer)
    framework = classification.get("agent_system", rel_path.parts[0] if len(rel_path.parts) > 0 else "")
    model = classification.get("model_normalized", rel_path.parts[1] if len(rel_path.parts) > 1 else "")
    failure_mode = classification.get("error_bucket", rel_path.parts[2] if len(rel_path.parts) > 2 else "")
    prompt_id = classification.get("prompt_index", rel_path.parts[3] if len(rel_path.parts) > 3 else "")
    trace_id = f"{classification.get('job_id', rel_path.stem)}:{classification.get('child_index', '')}".rstrip(":")

    return {
        "trace_id": trace_id,
        "source_path": str(source_path),
        "relative_path": rel_path.as_posix(),
        "framework": framework,
        "underlying_model": model,
        "failure_mode": failure_mode,
        "prompt_id": prompt_id,
        "original_token_estimate": original_tokens,
        "cleaned_token_estimate": cleaned_tokens,
        "token_estimator": tokenizer,
        "compression_ratio": round(cleaned_tokens / original_tokens, 6) if original_tokens else 1.0,
        "rules_applied": sorted(cleaned.rules_applied),
        "preserved_counts": count_preserved_items(cleaned.text),
        "collapsed_content_summaries": [
            {
                "rule": event.rule,
                "reason": event.reason,
                "source_lines": [event.start_line, event.end_line],
                "omitted_lines": event.omitted_lines,
                "omitted_chars": event.omitted_chars,
                "excerpt_start": event.excerpt_start,
                "excerpt_end": event.excerpt_end,
                "possible_evidence_loss": event.possible_evidence_loss,
            }
            for event in cleaned.collapses
        ],
        "removed_content_summaries": cleaned.removed_content_summaries,
        "possible_evidence_loss": sorted(set(cleaned.possible_evidence_loss)) or ["none identified"],
        "output_paths": {
            "cleaned_trace": str(out_dir / "cleaned_trace.txt"),
            "cleaning_manifest": str(out_dir / "cleaning_manifest.json"),
        },
    }


def should_skip_path(path: Path) -> bool:
    return any(marker in path.as_posix() for marker in SKIP_PATH_MARKERS)


def iter_logs(source_root: Path, include_skipped: bool = False) -> Iterable[Path]:
    for path in sorted(source_root.rglob("*.log")):
        if not include_skipped and should_skip_path(path.relative_to(source_root)):
            continue
        yield path


def count_skipped_logs(source_root: Path, include_skipped: bool = False) -> int:
    if include_skipped:
        return 0
    return sum(1 for path in source_root.rglob("*.log") if should_skip_path(path.relative_to(source_root)))


def run(source_root: Path, output_root: Path, tokenizer: str, include_skipped: bool = False) -> dict[str, object]:
    if not source_root.exists():
        raise SystemExit(f"source root does not exist: {source_root}")

    totals = {
        "source_files": 0,
        "original_tokens": 0,
        "cleaned_tokens": 0,
        "skipped_files": count_skipped_logs(source_root, include_skipped),
    }
    by_framework: dict[str, Counter[str]] = defaultdict(Counter)
    by_failure: dict[str, Counter[str]] = defaultdict(Counter)

    output_root.mkdir(parents=True, exist_ok=True)

    for source_path in iter_logs(source_root, include_skipped):
        rel_path = source_path.relative_to(source_root)
        original_text = source_path.read_text(encoding="utf-8", errors="replace")
        classification = parse_classification(original_text)
        framework = classification.get("agent_system", rel_path.parts[0] if rel_path.parts else "")
        cleaned = clean_text(original_text, framework)
        out_dir = trace_output_dir(output_root, rel_path)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "cleaned_trace.txt").write_text(cleaned.text, encoding="utf-8")
        manifest = manifest_for(source_path, rel_path, out_dir, classification, original_text, cleaned, tokenizer)
        (out_dir / "cleaning_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        original_tokens = int(manifest["original_token_estimate"])
        cleaned_tokens = int(manifest["cleaned_token_estimate"])
        totals["source_files"] += 1
        totals["original_tokens"] += original_tokens
        totals["cleaned_tokens"] += cleaned_tokens
        by_framework[framework]["files"] += 1
        by_framework[framework]["original_tokens"] += original_tokens
        by_framework[framework]["cleaned_tokens"] += cleaned_tokens
        failure_mode = str(manifest["failure_mode"])
        by_failure[f"{framework}/{failure_mode}"]["files"] += 1
        by_failure[f"{framework}/{failure_mode}"]["original_tokens"] += original_tokens
        by_failure[f"{framework}/{failure_mode}"]["cleaned_tokens"] += cleaned_tokens

    compression = (
        totals["cleaned_tokens"] / totals["original_tokens"] if totals["original_tokens"] else 1.0
    )
    stats: dict[str, object] = {
        **totals,
        "compression_ratio": compression,
        "by_framework": {key: dict(value) for key, value in sorted(by_framework.items())},
        "by_framework_failure": {key: dict(value) for key, value in sorted(by_failure.items())},
    }
    write_readme(output_root, source_root, tokenizer, stats)
    (output_root / "cleaning_summary.json").write_text(
        json.dumps(stats, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--tokenizer",
        choices=("char4", "tiktoken"),
        default="char4",
        help="Token estimator for manifests. tiktoken falls back to char4 if unavailable.",
    )
    parser.add_argument(
        "--include-skipped",
        action="store_true",
        help="Include paths that would normally be skipped, such as __vanilla strata.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    stats = run(args.source_root, args.output_root, args.tokenizer, args.include_skipped)
    print(
        "Cleaned {source_files} traces (skipped {skipped_files}): {original_tokens:,} -> {cleaned_tokens:,} "
        "estimated tokens (ratio {compression_ratio:.3f})".format(**stats)
    )
    for framework, row in stats["by_framework"].items():  # type: ignore[index,union-attr]
        original = row["original_tokens"]
        cleaned = row["cleaned_tokens"]
        ratio = cleaned / original if original else 1.0
        print(f"  {framework}: {row['files']} files, {original:,} -> {cleaned:,} ({ratio:.3f})")


if __name__ == "__main__":
    main()
