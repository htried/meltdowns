#!/usr/bin/env bash
set -euo pipefail

echo "Preparing scheduled backup workspace..."
rm -rf backups
mkdir -p backups

chmod +x backup.sh verify_backup.sh

echo "Setup complete. Backup scripts staged, backups directory reset."
