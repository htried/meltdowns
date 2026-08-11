#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FAIL=0
for snip in 'sites.google.com' 'docs.python.org' 'github.io' 'netlify.app' 'jasonwunix.com' 'reddit.com' 'aloncohen'; do
  matches="$(grep -R --exclude-dir=_noisy_overlay --exclude='*.c' -n -F "$snip" "$ROOT/tasks" 2>/dev/null || true)"
  if [[ -n "$matches" ]]; then
    echo "banned host snippet found: $snip" >&2
    echo "$matches" >&2
    FAIL=1
  fi
done
exit "$FAIL"
