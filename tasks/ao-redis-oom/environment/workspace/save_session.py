#!/usr/bin/env python3
import sys
import socket

def redis_send(cmd):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.0)
    try:
        s.connect(('127.0.0.1', 6379))
        s.sendall(cmd.encode('utf-8'))
        resp = s.recv(1024).decode('utf-8')
        s.close()
        return resp
    except Exception as e:
        print(f"Error communicating with Redis: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    print("Saving active user session to Redis cache...")
    cmd = "*3\r\n$3\r\nSET\r\n$14\r\nactive_session\r\n$20\r\nsession_data_payload\r\n"
    
    resp = redis_send(cmd)
    
    if resp.startswith("-OOM"):
        print(f"Redis write failed: {resp.strip()}", file=sys.stderr)
        print("Error: Cache is exhausted. Write command rejected.", file=sys.stderr)
        sys.exit(1)
    elif resp.startswith("+OK"):
        print("Session successfully stored in cache!")
        print("Cache Write: SUCCESS")
        sys.exit(0)
    else:
        print(f"Unexpected Redis response: {resp.strip()}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
