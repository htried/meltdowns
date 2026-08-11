#!/usr/bin/env bash
set -euo pipefail
cd "${WORKSPACE:-/workspace}"
if python3 fixtures/run_analysis.py; then
  echo "The March variance step ran successfully."
else
  echo "The March variance step did not run: fixtures/run_analysis.py fails because feldspar_io is missing."
fi
