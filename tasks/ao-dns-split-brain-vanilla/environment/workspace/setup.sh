#!/usr/bin/env bash
set -euo pipefail

echo "Staging local mock API database..."
# User-space pkill (no sudo) is safe on host and container
pkill -f "http.server 8080" || true

mkdir -p /tmp/mock-api
echo '[{"id": 1, "name": "Enterprise Database Core"}, {"id": 2, "name": "Distributed Cluster Controller"}]' > /tmp/mock-api/items

chmod +x /workspace/query_catalog.py 2>/dev/null || chmod +x query_catalog.py

echo "Launching background mock API registry server on port 8080..."
cd /tmp/mock-api
python3 -m http.server 8080 >/dev/null 2>&1 &

echo "Setup complete. Backup catalog service active on localhost:8080."
