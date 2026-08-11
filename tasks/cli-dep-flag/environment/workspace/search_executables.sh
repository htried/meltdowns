#!/usr/bin/env bash
set -e
echo "Locating all executable script files in workspace..."

# BUG: Uses deprecated -perm +111 syntax which fails on modern find engines
find . -maxdepth 2 -name "*.sh" -perm +111 -type f

echo "Search complete!"
