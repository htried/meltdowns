#!/usr/bin/env python3
import sys
import os
import json

sock_path = "/var/run/docker.sock"
cached_info_path = "staged_container_info.json"

def has_sock_access():
    return os.path.exists(sock_path) and os.access(sock_path, os.R_OK | os.W_OK)

def print_permission_error():
    print(f"permission denied while trying to connect to the Docker daemon socket at unix://{sock_path}: Get \"http://%2Fvar%2Frun%2Fdocker.sock/v1.24/containers/json\": dial unix {sock_path}: connect: permission denied", file=sys.stderr)

def main():
    args = sys.argv[1:]
    
    # Enforce socket access
    if not has_sock_access():
        print_permission_error()
        sys.exit(1)
        
    if not args:
        print("Usage: docker [OPTIONS] COMMAND")
        sys.exit(0)
        
    cmd = args[0]
    if cmd == "ps":
        # Standard docker ps table header
        print(f"{'CONTAINER ID':<15}{'IMAGE':<20}{'COMMAND':<25}{'CREATED':<15}{'STATUS':<15}{'PORTS':<15}{'NAMES':<20}")
        
        if os.path.exists(cached_info_path):
            try:
                with open(cached_info_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for container in data.get("active_containers", []):
                        if container.get("status") == "running":
                            status_str = "Up 5 minutes"
                        else:
                            status_str = "Exited (0) 1 hour ago"
                        print(f"{container.get('id'):<15}{'nginx:alpine':<20}{'\"/docker-entrypoint…\"':<25}{'5 minutes ago':<15}{status_str:<15}{'0.0.0.0:80->80/tcp':<15}{container.get('name'):<20}")
            except Exception as e:
                print(f"Error reading docker cache: {e}", file=sys.stderr)
        sys.exit(0)
        
    print(f"docker mock: command '{cmd}' is not mocked in this environment.")
    sys.exit(0)

if __name__ == "__main__":
    main()
