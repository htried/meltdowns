#!/usr/bin/env bash
set -euo pipefail

mkdir -p backups
TIMESTAMP=$(date +%s)
echo "Backup data compiled at $(date)" > "backups/backup_${TIMESTAMP}.txt"
echo "Backup completed: backup_${TIMESTAMP}.txt"
