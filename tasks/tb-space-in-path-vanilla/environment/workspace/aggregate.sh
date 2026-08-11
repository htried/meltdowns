#!/usr/bin/env bash
set -e
echo "Aggregating monthly reports..."

# Find all text files in reports directory
for filepath in reports/*.txt; do
  echo "Processing $filepath..."
  # Quoted variables prevent splitting on spaces
  cat "$filepath"
  echo ""
done

echo "Aggregation successful!"
