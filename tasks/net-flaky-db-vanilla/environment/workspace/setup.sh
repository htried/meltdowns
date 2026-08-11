#!/usr/bin/env bash
set -euo pipefail

echo "Cleaning up any old database socket listeners..."
# User-space pkill
pkill -f "socket.AF_INET" || true

echo "Starting background mock database port 5432 socket listener..."
# Run socket listener in background
python3 -c '
import socket
import sys
import time
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    s.bind(("127.0.0.1", 5432))
    s.listen(5)
    while True:
        conn, addr = s.accept()
        conn.close()
except Exception as e:
    sys.exit(1)
' >/dev/null 2>&1 &

# Wait a moment for socket to bind
sleep 0.5

echo "Configuring loopback redirect for local offline connection success..."
echo "DB_IP=127.0.0.1" > /tmp/setup_env

chmod +x query_db.py
echo "Setup complete. Mock local database active on port 5432."
