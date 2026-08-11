#!/usr/bin/env bash
set -euo pipefail

# Ensure target backups directory exists
mkdir -p backups

# Generate a unique timestamped backup file
TIMESTAMP=$(date +%s)
echo "Backup data compiled at $(date)" > "backups/backup_${TIMESTAMP}.txt"
echo "Backup completed: backup_${TIMESTAMP}.txt"
