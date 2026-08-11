#!/usr/bin/env bash
set -euo pipefail

echo "Cleaning up existing mock Redis servers..."
sudo pkill -f "redis_service.py" || true

echo "Launching background mock Redis OOM service on port 6379..."
chmod +x redis_service.py save_session.py

# Launch the background socket listener
python3 redis_service.py >/dev/null 2>&1 &

echo "Setup complete. Mock Redis server active on localhost:6379 under noeviction policy."
