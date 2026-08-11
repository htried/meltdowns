#!/usr/bin/env bash
set -euo pipefail
if [ ! -f /workspace/close-pack/prior_summary.txt ]; then
  echo "prior_summary.txt is missing under /workspace/close-pack, so I cannot produce the requested two-sentence gist."
else
  head -n 5 /workspace/close-pack/prior_summary.txt
fi
