#!/usr/bin/env bash
set -euo pipefail

echo "Preparing SSH known_hosts files..."
# Initialize an empty known_hosts file
: > known_hosts

echo "Staging company remote server public host key..."
mkdir -p keys
cp git_server_key.pub keys/git_server_key.pub

chmod +x sync_code.py

echo "Setup complete. Empty known_hosts staged, public host key stored in keys/."
