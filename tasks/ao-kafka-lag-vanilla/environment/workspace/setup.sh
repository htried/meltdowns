#!/usr/bin/env bash
set -euo pipefail

echo "Generating clean queue log..."
: > queue_log.jsonl

# Write 50 valid JSON lines (no poison pill!)
for i in $(seq 1 50); do
  val=$((i * 10 + 5))
  echo "{\"id\": $i, \"metric\": \"cpu\", \"val\": $val}" >> queue_log.jsonl
done

# Initialize offset to 0
echo "0" > offset.txt

chmod +x consumer.py

echo "Setup complete. Clean queue staged successfully."
