#!/usr/bin/env bash
set -euo pipefail
REWARD_FILE="${REWARD_FILE:-/logs/verifier/reward.txt}"
OUT_DIR="$(dirname "$REWARD_FILE")"
mkdir -p "$OUT_DIR"
export REWARD_FILE OUT_DIR
export AGENT_LOGS="${AGENT_LOGS:-/logs/agent}"
export TAXONOMY_FRAMEWORK="${TAXONOMY_FRAMEWORK:-opencode}"
export TAXONOMY_JUDGE_MODEL="${TAXONOMY_JUDGE_MODEL:-gpt-4o-mini}"

python3 -m pip install -q openai python-dotenv >/tmp/grader-pip.log 2>&1 || {
  echo "0.0" > "$REWARD_FILE"
  echo '{"error":"pip install openai/python-dotenv failed"}' > "$OUT_DIR/verifier_error.json"
  exit 0
}

# Prefer instruction copied beside tests when Harbor mounts /tests.
INSTRUCTION=""
for candidate in /tests/instruction.md /workspace/instruction.md; do
  if [ -f "$candidate" ]; then INSTRUCTION="$candidate"; break; fi
done

ARGS=(python3 /tests/grader/run_grade_container.py --out-dir "$OUT_DIR" --agent-logs "$AGENT_LOGS" --framework "$TAXONOMY_FRAMEWORK")
if [ -n "$INSTRUCTION" ]; then
  ARGS+=(--instruction-file "$INSTRUCTION")
fi
"${ARGS[@]}" || true
if [ ! -f "$REWARD_FILE" ]; then
  echo "0.0" > "$REWARD_FILE"
fi
