#!/usr/bin/env bash
set -euo pipefail

echo "Preparing SSH known_hosts file..."
# Pre-populate the server host key inside known_hosts so it's pre-authorized!
echo "git.internal.company.com ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBEMvVjI3NnpxN00ydU5VdnkrdWRXSDZtY3d3TmxmQ0wrcWZPQU9yZ3pIV3d0c3p4NTV0NlZxeWlyTjR0NlBia1pNVzE0TkF6WnZsdU4vNUZ5UGsvY2c9PQ==" > known_hosts

echo "Staging company remote server public host key..."
mkdir -p keys
cp git_server_key.pub keys/git_server_key.pub

chmod +x sync_code.py

echo "Setup complete. Pre-authorized known_hosts staged, public host key stored in keys/."
