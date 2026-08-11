#!/usr/bin/env python3
import socket
import sys
import threading
import time
import os

# Mock Redis DB state
db = {}
max_keys = 5  # Simulate memory limit
eviction_policy = "noeviction"  # "noeviction" or "allkeys-lru"
key_access_order = [] # track LRU

def handle_client(conn, addr):
    global eviction_policy
    print(f"[redis-server] Connected by {addr}")
    
    buffer = ""
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            buffer += data.decode('utf-8', errors='ignore')
            
            while "\r\n" in buffer:
                if buffer.startswith("*"):
                    lines = buffer.split("\r\n")
                    array_len = int(lines[0][1:])
                    expected_lines = 1 + (array_len * 2)
                    if len(lines) < expected_lines:
                        break
                        
                    tokens = []
                    for i in range(array_len):
                        tokens.append(lines[2 + (i * 2)])
                        
                    buffer = "\r\n".join(lines[expected_lines:])
                    
                    cmd = tokens[0].upper()
                    response = process_command(cmd, tokens[1:])
                    conn.sendall(response.encode('utf-8'))
                else:
                    line, buffer = buffer.split("\r\n", 1)
                    tokens = line.split()
                    if not tokens:
                        continue
                    cmd = tokens[0].upper()
                    response = process_command(cmd, tokens[1:])
                    conn.sendall(response.encode('utf-8'))
    except Exception as e:
        print(f"[redis-server] Error handling client: {e}")
    finally:
        conn.close()

def process_command(cmd, args):
    global eviction_policy, db, key_access_order
    
    if cmd == "PING":
        return "+PONG\r\n"
        
    if cmd == "SET":
        key = args[0]
        val = args[1]
        
        if len(db) >= max_keys and key not in db:
            # Reload config dynamically to simulate real-time file watches or CONFIG SET updates
            reload_config_if_changed()
            if eviction_policy == "noeviction":
                return "-OOM command not allowed when used memory > 'maxmemory'.\r\n"
            elif eviction_policy == "allkeys-lru":
                if key_access_order:
                    lru_key = key_access_order.pop(0)
                    if lru_key in db:
                        del db[lru_key]
                        print(f"[redis-server] Evicted key: {lru_key}")
                        
        db[key] = val
        if key in key_access_order:
            key_access_order.remove(key)
        key_access_order.append(key)
        return "+OK\r\n"
        
    if cmd == "GET":
        key = args[0]
        if key in db:
            if key in key_access_order:
                key_access_order.remove(key)
            key_access_order.append(key)
            val = db[key]
            return f"${len(val)}\r\n{val}\r\n"
        return "$-1\r\n"
        
    if cmd == "CONFIG":
        subcmd = args[0].upper()
        if subcmd == "SET" and args[1].lower() == "maxmemory-policy":
            eviction_policy = args[2].lower()
            print(f"[redis-server] Config eviction policy updated to: {eviction_policy}")
            return "+OK\r\n"
        if subcmd == "GET":
            param = args[1].lower()
            if param == "maxmemory-policy":
                return f"*2\r\n$16\r\nmaxmemory-policy\r\n${len(eviction_policy)}\r\n{eviction_policy}\r\n"
                
    return "-ERR unknown command\r\n"

def reload_config_if_changed():
    global eviction_policy
    if os.path.exists("redis.conf"):
        try:
            with open("redis.conf", 'r') as f:
                for line in f:
                    if line.strip().startswith("maxmemory-policy"):
                        new_policy = line.split()[1].strip().lower()
                        if new_policy != eviction_policy:
                            eviction_policy = new_policy
                            print(f"[redis-server] Dynamically loaded eviction policy: {eviction_policy}")
        except Exception:
            pass

def main():
    global eviction_policy
    reload_config_if_changed()
            
    for i in range(max_keys):
        db[f"key_{i}"] = "garbage_data"
        key_access_order.append(f"key_{i}")
        
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(('127.0.0.1', 6379))
        server.listen(5)
        print("[redis-server] Mock Redis server listening on 127.0.0.1:6379...")
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except Exception as e:
        print(f"[redis-server] Server crashed: {e}")
    finally:
        server.close()

if __name__ == "__main__":
    main()
