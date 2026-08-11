#!/usr/bin/env bash
set -euo pipefail

echo "Staging tar archive..."
# Create dummy assets
mkdir -p assets
echo "console.log('Web Asset Staged successfully');" > assets/main.js

# Create the archive using the real system tar (mock is not installed yet)
tar -czf assets.tar.gz assets/
rm -rf assets/

echo "Installing BSD-simulated Nginx/tar wrapper..."
# Install mock tar to /usr/local/bin/tar to override the default command
sudo cp tar_mock.py /usr/local/bin/tar
sudo chmod +x /usr/local/bin/tar

chmod +x deploy.sh

echo "Setup complete. Portable tar test environment staged."
