#!/usr/bin/env bash
set -euo pipefail

echo "Installing mock Nginx service to user space (.venv/bin)..."
mkdir -p .venv/bin
cp nginx_mock.py .venv/bin/nginx
chmod +x .venv/bin/nginx

# Set up web document directories
mkdir -p html
echo "<h1>Nginx Web Proxy Hello</h1>" > html/index.html

echo "Setup complete. Mock Nginx binary staged in user-space."
