#!/usr/bin/env bash
set -euo pipefail
cd "${WORKSPACE:-/workspace}"
python3 - <<'PY'
from pathlib import Path
p = Path("query_db.py")
text = p.read_text()
text = text.replace(
    "def main():\n    try:\n        connect_and_query()\n    except (socket.error, ConnectionError) as e:\n        print(f\"Database connection failed: {e}\", file=sys.stderr)\n        sys.exit(1)\n",
    "def main():\n    last = None\n    for attempt in range(1, 8):\n        try:\n            connect_and_query()\n            return\n        except (socket.error, ConnectionError) as e:\n            last = e\n            print(f\"Transient database failure on attempt {attempt}: {e}\", file=sys.stderr)\n    print(f\"Database connection failed after retries: {last}\", file=sys.stderr)\n    sys.exit(1)\n",
)
p.write_text(text)
PY
python3 query_db.py
