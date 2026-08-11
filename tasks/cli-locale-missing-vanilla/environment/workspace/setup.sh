#!/usr/bin/env bash
set -euo pipefail

echo "Staging vanilla locale (C.UTF-8)..."
echo "LANG=C.UTF-8" > /tmp/setup_env
echo "LC_ALL=" >> /tmp/setup_env

chmod +x process_data.py
echo "Setup complete. Valid locale pre-configured."
