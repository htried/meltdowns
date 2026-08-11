#!/usr/bin/env bash
set -euo pipefail

echo "Preparing scheduled backup workspace..."
rm -rf backups
mkdir -p backups

chmod +x backup.sh verify_backup.sh

# Run backup directly during setup to simulate a functioning schedule out-of-the-box
./backup.sh

echo "Setup complete. Backup scripts staged, initial backup successfully performed."
