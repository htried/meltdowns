#!/usr/bin/env bash
set -euo pipefail

echo "Setting up keys and permissions..."
mkdir -p keys
echo "-----BEGIN RSA PRIVATE KEY-----" > keys/id_rsa
echo "MIIEogIBAAKCAQEAnzRhMTVKdHJzR2VuZXJhdGVkTW9ja0tle..." >> keys/id_rsa
echo "-----END RSA PRIVATE KEY-----" >> keys/id_rsa

chmod 644 keys/id_rsa
chmod +x sync.py
echo "Setup complete. Insecure key created with 0644 permissions."
