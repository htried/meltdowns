#!/usr/bin/env bash
set -euo pipefail
chmod +x /workspace/query_db.py
python /opt/flaky_db_server.py &
exec sleep infinity
