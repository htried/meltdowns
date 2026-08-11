#!/usr/bin/env python3
import sys
import json
import os

queue_path = "queue_log.jsonl"
offset_path = "offset.txt"

def read_offset():
    if not os.path.exists(offset_path):
        return 0
    try:
        with open(offset_path, 'r') as f:
            return int(f.read().strip())
    except Exception:
        return 0

def save_offset(offset):
    with open(offset_path, 'w') as f:
        f.write(str(offset))

def main():
    start_offset = read_offset()
    print(f"Starting consumer from offset: {start_offset}")
    
    if not os.path.exists(queue_path):
        print(f"Error: queue log {queue_path} not found.", file=sys.stderr)
        sys.exit(1)
        
    with open(queue_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    total_lines = len(lines)
    if start_offset >= total_lines:
        print("All messages processed. Queue is caught up.")
        print("Consumer successfully finished processing.")
        sys.exit(0)
        
    for idx in range(start_offset, total_lines):
        line = lines[idx]
        
        # Parses cleanly on valid JSON
        payload = json.loads(line)
        
        print(f"Processed offset {idx}: ID={payload.get('id')}, Val={payload.get('val')}")
        save_offset(idx + 1)
        
    print("Consumer successfully finished processing.")

if __name__ == "__main__":
    main()
