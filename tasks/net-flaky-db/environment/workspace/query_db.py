#!/usr/bin/env python3
import os
import socket
import sys

db_ip = os.environ.get("DB_IP", "127.0.0.1")
db_port = int(os.environ.get("DB_PORT", "5432"))

def connect_and_query():
    print(f"Connecting to database at {db_ip}:{db_port}...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.0)
    # BUG: no retry logic. The fixture server drops every other request before returning OK.
    s.connect((db_ip, db_port))
    s.sendall(b"QUERY\n")
    resp = s.recv(1024)
    if resp.strip() != b"OK":
        raise ConnectionError(f"bad response from database: {resp!r}")
    print("Successfully established database session.")
    print("Querying records...")
    print("Database Query: SUCCESS")
    s.close()

def main():
    try:
        connect_and_query()
    except (socket.error, ConnectionError) as e:
        print(f"Database connection failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
