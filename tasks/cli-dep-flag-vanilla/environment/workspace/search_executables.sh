#!/usr/bin/env bash
set -e
echo "Locating all executable script files in workspace..."

# Standard modern GNU find syntax resolves and succeeds cleanly
find . -maxdepth 2 -name "*.sh" -perm /111 -type f

echo "Search complete: SUCCESS"
