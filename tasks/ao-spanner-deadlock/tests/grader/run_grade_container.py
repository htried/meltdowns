#!/usr/bin/env python3
"""Container-friendly grader entrypoint (no repo package import required)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from grade import GradeResult, grade_transcript, write_grade_artifacts  # noqa: E402


def _find_transcript(explicit: Path | None, agent_logs: Path) -> Path | None:
    if explicit is not None and explicit.exists():
        return explicit
    preferred = [
        "opencode.txt",
        "codex.txt",
        "trajectory.json",
        "agent.log",
        "stdout.log",
        "transcript.txt",
    ]
    for name in preferred:
        path = agent_logs / name
        if path.exists() and path.stat().st_size > 0:
            return path
    if agent_logs.exists():
        for path in sorted(agent_logs.rglob("*")):
            if path.is_file() and path.suffix in {".txt", ".log", ".json"} and path.stat().st_size > 0:
                return path
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transcript", type=Path, default=None)
    parser.add_argument("--agent-logs", type=Path, default=Path(os.environ.get("AGENT_LOGS", "/logs/agent")))
    parser.add_argument("--out-dir", type=Path, default=Path(os.environ.get("REWARD_DIR", "/logs/verifier")))
    parser.add_argument("--framework", default=os.environ.get("TAXONOMY_FRAMEWORK", "opencode"))
    parser.add_argument("--judge-model", default=os.environ.get("TAXONOMY_JUDGE_MODEL"))
    parser.add_argument("--instruction-file", type=Path, default=Path("/tests/instruction.md"))
    parser.add_argument(
        "--vanilla-authorized",
        action="store_true",
        default=os.environ.get("TAXONOMY_VANILLA_AUTHORIZED", "").lower() in {"1", "true", "yes"},
    )
    args = parser.parse_args()

    instruction = None
    if args.instruction_file and args.instruction_file.exists():
        instruction = args.instruction_file.read_text(encoding="utf-8")

    transcript_path = _find_transcript(args.transcript, args.agent_logs)
    if transcript_path is None:
        result = GradeResult(
            reward=0.0,
            measurement=None,
            error=f"transcript not found under {args.agent_logs}",
            cleaned_trace="",
            judge_model=args.judge_model or "gpt-4o-mini",
        )
    else:
        text = transcript_path.read_text(encoding="utf-8", errors="replace")
        result = grade_transcript(
            text,
            framework=args.framework,
            judge_model=args.judge_model,
            vanilla_authorized=args.vanilla_authorized,
            instruction=instruction,
        )

    write_grade_artifacts(args.out_dir, result)
    # Harbor convention: also mirror reward to REWARD_FILE if set.
    reward_file = Path(os.environ.get("REWARD_FILE", str(args.out_dir / "reward.txt")))
    reward_file.parent.mkdir(parents=True, exist_ok=True)
    reward_file.write_text(f"{result.reward:.1f}\n", encoding="utf-8")
    print(f"reward={result.reward} transcript={transcript_path} error={bool(result.error)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
