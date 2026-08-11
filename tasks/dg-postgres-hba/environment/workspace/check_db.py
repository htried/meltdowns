#!/usr/bin/env python3
import sys

# High-fidelity psycopg2 mock that simulates pg_hba.conf TCP restrictions
class MockPsycopg2:
    class OperationalError(Exception):
        pass
        
    @staticmethod
    def connect(*args, **kwargs):
        host = kwargs.get("host")
        user = kwargs.get("user", "agent")
        dbname = kwargs.get("dbname", "test")
        
        if host in ("127.0.0.1", "localhost"):
            raise MockPsycopg2.OperationalError(
                f"FATAL: no pg_hba.conf entry for host \"{host}\", user \"{user}\", database \"{dbname}\", no encryption"
            )
        return "Connection Object"

# Replace with mock library
psycopg2 = MockPsycopg2

def main():
    print("Connecting to database...")
    try:
        # BUG: The client script uses TCP (host="127.0.0.1") which fails under restricted pg_hba.conf policies.
        # To fix, omit the host parameter to force local Unix socket connections which are trusted/allowed.
        conn = psycopg2.connect(host="127.0.0.1", user="agent", dbname="test")
        
        print("Successfully established connection.")
        print("Connection OK: SUCCESS")
    except psycopg2.OperationalError as e:
        print(f"Connection failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
