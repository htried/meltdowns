#!/usr/bin/env bash
set -euo pipefail

echo "Staging tar archive..."
mkdir -p assets
echo "console.log('Web Asset Staged successfully');" > assets/main.js

# Create archive
tar -czf assets.tar.gz assets/
rm -rf assets/

chmod +x deploy.sh
echo "Setup complete. Portable tar environment staged."
