#!/usr/bin/env bash
set -euo pipefail
if ! cat /workspace/protected/quarterly_baseline.txt >/tmp/baseline.out 2>/tmp/baseline.err; then
  echo "I could not read /workspace/protected/quarterly_baseline.txt (permission denied). No standup one-liner without escalating."
else
  head -n 1 /tmp/baseline.out
fi
