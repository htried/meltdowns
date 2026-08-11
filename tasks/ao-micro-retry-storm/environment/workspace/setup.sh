#!/usr/bin/env bash
set -euo pipefail

echo "Cleaning up existing mock lagging servers..."
sudo pkill -f "slow_server.py" || true

echo "Launching background mock lagging downstream API on port 8081..."
chmod +x slow_server.py gateway.py

# Launch background listener
python3 slow_server.py >/dev/null 2>&1 &

echo "Setup complete. Lagging downstream service active on localhost:8081."
