#!/usr/bin/env bash
set -euo pipefail

echo "Installing mock Nginx service..."
# Install the mock python script to /usr/local/bin/nginx using sudo (since SETUP_CMD has root privileges)
sudo cp nginx_mock.py /usr/local/bin/nginx
sudo chmod +x /usr/local/bin/nginx

# Set up web document directories
mkdir -p /workspace/html
echo "<h1>Nginx Web Proxy Hello</h1>" > /workspace/html/index.html

echo "Setup complete. Mock Nginx binary staged in /usr/local/bin/nginx."
