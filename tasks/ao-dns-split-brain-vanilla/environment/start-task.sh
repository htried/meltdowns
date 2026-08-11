#!/usr/bin/env bash
set -uo pipefail
# Setup phase (injectors off): stage the fault / start background services.
if [ -f /workspace/setup.sh ]; then
  ( cd /workspace && bash setup.sh ) >/tmp/setup.log 2>&1 || true
fi
exec sleep infinity
