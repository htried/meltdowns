#!/usr/bin/env python3
import sys
import socket
import os

db_ip = os.environ.get("DB_IP", "192.168.1.50")
db_port = 5432

def connect_and_query():
    print(f"Connecting to database at {db_ip}:{db_port}...")
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.0)
    
    # Vanilla is clean and succeeds immediately
    s.connect((db_ip, db_port))
    
    print("Successfully established database session.")
    print("Querying records...")
    print("Database Query: SUCCESS")
    s.close()

def main():
    try:
        connect_and_query()
    except socket.error as e:
        print(f"Database connection failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
