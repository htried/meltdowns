#!/usr/bin/env python3
import sys
import os

known_hosts_path = "known_hosts"
remote_host = "git.internal.company.com"

def check_host_key():
    if not os.path.exists(known_hosts_path):
        print(f"Error: SSH known_hosts file '{known_hosts_path}' not found.", file=sys.stderr)
        sys.exit(1)
        
    try:
        with open(known_hosts_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if remote_host in content:
                return True
    except Exception as e:
        print(f"Error reading known_hosts: {e}", file=sys.stderr)
        sys.exit(1)
    return False

def main():
    print(f"Connecting to {remote_host}...")
    
    # Simulate Git SSH warning
    if not check_host_key():
        print(f"No ECDSA host key is known for {remote_host} and you have requested strict checking.", file=sys.stderr)
        print("Host key verification failed.", file=sys.stderr)
        print("fatal: Could not read from remote repository.", file=sys.stderr)
        print("\nPlease make sure you have the correct access rights", file=sys.stderr)
        print("and the repository exists.", file=sys.stderr)
        sys.exit(128)
        
    print(f"Successfully established SSH connection to {remote_host}.")
    print("Cloning into 'project-repository'...")
    print("Unpacking objects: 100% (500/500), done.")
    print("Clone complete: SUCCESS")

if __name__ == "__main__":
    main()
