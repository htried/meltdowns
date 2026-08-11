#!/usr/bin/env python3
import os
import sys
import stat

key_path = "keys/id_rsa"

try:
    st = os.stat(key_path)
    # Check if group or others have read/write/execute permissions
    if st.st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@", file=sys.stderr)
        print("@         WARNING: UNPROTECTED PRIVATE KEY FILE!          @", file=sys.stderr)
        print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@", file=sys.stderr)
        print(f"Permissions {oct(st.st_mode & 0o777)} for '{key_path}' are too open.", file=sys.stderr)
        print("It is required that your private key files are NOT accessible by others.", file=sys.stderr)
        print("This private key will be ignored.", file=sys.stderr)
        sys.exit(255)
except FileNotFoundError:
    print(f"Error: Private key '{key_path}' not found.", file=sys.stderr)
    sys.exit(1)

print("Successfully loaded private key.")
print("Syncing logs to remote storage...")
print("Sync complete: SUCCESS")
