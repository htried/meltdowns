#!/usr/bin/env python3
"""CLI entrypoint for Harbor meltdown taxonomy grading."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from bounded_recovery_sft.harbor_meltdown.verifier.grade import (
    grade_transcript,
    write_grade_artifacts,
)


def _find_transcript(explicit: Path | None, agent_logs: Path) -> Path | None:
    if explicit is not None and explicit.exists():
        return explicit
    candidates = [
        agent_logs / "trajectory.json",
        agent_logs / "agent.log",
        agent_logs / "stdout.log",
        agent_logs / "transcript.txt",
        agent_logs / "opencode.log",
        agent_logs / "codex.log",
    ]
    for path in candidates:
        if path.exists() and path.stat().st_size > 0:
            return path
    if agent_logs.exists():
        texts = sorted(agent_logs.rglob("*.txt")) + sorted(agent_logs.rglob("*.log"))
        for path in texts:
            if path.stat().st_size > 0:
                return path
    return None


def _read_transcript(path: Path) -> str:
    if path.suffix == ".json":
        text = path.read_text(encoding="utf-8", errors="replace")
        # Keep raw JSON text for the judge; cleaner will collapse noise.
        return text
    return path.read_text(encoding="utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transcript", type=Path, default=None)
    parser.add_argument("--agent-logs", type=Path, default=Path("/logs/agent"))
    parser.add_argument("--out-dir", type=Path, default=Path("/logs/verifier"))
    parser.add_argument("--framework", default=os.environ.get("TAXONOMY_FRAMEWORK", "opencode"))
    parser.add_argument("--judge-model", default=None)
    parser.add_argument("--instruction-file", type=Path, default=None)
    parser.add_argument(
        "--vanilla-authorized",
        action="store_true",
        default=os.environ.get("TAXONOMY_VANILLA_AUTHORIZED", "").lower() in {"1", "true", "yes"},
    )
    args = parser.parse_args()

    transcript_path = _find_transcript(args.transcript, args.agent_logs)
    instruction = None
    if args.instruction_file and args.instruction_file.exists():
        instruction = args.instruction_file.read_text(encoding="utf-8")

    if transcript_path is None:
        from bounded_recovery_sft.harbor_meltdown.verifier.grade import GradeResult

        result = GradeResult(
            reward=0.0,
            measurement=None,
            error="transcript not found under agent logs",
            cleaned_trace="",
            judge_model=args.judge_model or os.environ.get("TAXONOMY_JUDGE_MODEL") or "gpt-4o-mini",
        )
    else:
        result = grade_transcript(
            _read_transcript(transcript_path),
            framework=args.framework,
            judge_model=args.judge_model,
            vanilla_authorized=args.vanilla_authorized,
            instruction=instruction,
        )

    write_grade_artifacts(args.out_dir, result)
    print(f"reward={result.reward} error={result.error is not None} out={args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
