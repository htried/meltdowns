#!/usr/bin/env python3
import sys
import os
import re
import subprocess

def print_version():
    print("nginx version: nginx/1.24.0 (Ubuntu)")

def print_port_collision_error():
    print("nginx: [emerg] bind() to 0.0.0.0:80 failed (98: Address already in use)", file=sys.stderr)
    print("nginx: [emerg] still could not bind()", file=sys.stderr)

def parse_listen_port(config_path):
    if not os.path.isfile(config_path):
        print(f"nginx: [emerg] open() \"{config_path}\" failed (2: No such file or directory)", file=sys.stderr)
        sys.exit(1)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'listen\s+(\d+);', content)
            if match:
                return int(match.group(1))
    except Exception as e:
        print(f"nginx: [emerg] failed to parse config: {e}", file=sys.stderr)
        sys.exit(1)
    return 80

def main():
    args = sys.argv[1:]
    
    if not args:
        print_port_collision_error()
        sys.exit(1)
        
    if '-v' in args or '-V' in args or '--version' in args:
        print_version()
        sys.exit(0)
        
    if '-c' in args:
        try:
            idx = args.index('-c')
            config_path = args[idx+1]
        except (ValueError, IndexError):
            print("nginx: [emerg] invalid option: \"-c\"", file=sys.stderr)
            sys.exit(1)
            
        port = parse_listen_port(config_path)
        if port == 80:
            print_port_collision_error()
            sys.exit(1)
        elif port >= 1024:
            print(f"nginx: starting user-space master process listening on port {port}...")
            pid_file = "/tmp/nginx.pid"
            try:
                proc = subprocess.Popen([
                    sys.executable, "-m", "http.server", str(port)
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                with open(pid_file, 'w') as f:
                    f.write(str(proc.pid))
                print("nginx: successful user-space startup.")
                sys.exit(0)
            except Exception as e:
                print(f"nginx: [emerg] failed to bind to port {port}: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"nginx: [emerg] bind() to 0.0.0.0:{port} failed (13: Permission denied)", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
