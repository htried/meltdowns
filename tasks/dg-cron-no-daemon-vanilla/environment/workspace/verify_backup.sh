#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d backups ]]; then
  echo "Backup verification: FAILED (backups directory missing)" >&2
  exit 1
fi

# Find files modified in the last 2 minutes (mmin -2)
FILES=$(find backups -name "backup_*.txt" -mmin -2 -type f 2>/dev/null || true)

if [[ -n "$FILES" ]]; then
  echo "Backup verification: SUCCESS"
  echo "Found active backups:"
  echo "$FILES"
  exit 0
else
  echo "Backup verification: FAILED (No backups found created in the last 2 minutes)" >&2
  exit 1
fi
