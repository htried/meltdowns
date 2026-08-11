#!/usr/bin/env bash
set -euo pipefail

echo "Initializing database orders.db..."
rm -f orders.db

# Seed the schema and rows using inline python
python3 - <<'PY'
import sqlite3
conn = sqlite3.connect("orders.db")
c = conn.cursor()
c.execute("CREATE TABLE inventory (id INTEGER PRIMARY KEY, quantity INTEGER)")
c.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, status TEXT)")
c.execute("INSERT INTO inventory (id, quantity) VALUES (1, 100)")
c.execute("INSERT INTO orders (id, status) VALUES (1, 'pending')")
conn.commit()
conn.close()
PY

chmod +x process_orders.py
echo "Setup complete. Database initialized and permissions set."
