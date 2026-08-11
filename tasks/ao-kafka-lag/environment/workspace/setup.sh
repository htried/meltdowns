#!/usr/bin/env bash
set -euo pipefail

echo "Generating queue log with poison pill at offset 44..."
: > queue_log.jsonl

# Write 44 valid JSON lines (offsets 0 to 43)
for i in $(seq 1 44); do
  val=$((i * 10 + 5))
  echo "{\"id\": $i, \"metric\": \"cpu\", \"val\": $val}" >> queue_log.jsonl
done

# Write the poison pill corrupt JSON line at offset 44 (45th line)
echo "{\"id\": 45, \"metric\": \"cpu\", \"val\":" >> queue_log.jsonl

# Write remaining 5 valid JSON lines (offsets 45 to 49)
for i in $(seq 46 50); do
  val=$((i * 10 + 5))
  echo "{\"id\": $i, \"metric\": \"cpu\", \"val\": $val}" >> queue_log.jsonl
done

# Initialize offset to 0
echo "0" > offset.txt

chmod +x consumer.py

echo "Setup complete. Queue staged with poison pill."
