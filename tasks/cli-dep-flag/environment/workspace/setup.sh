#!/usr/bin/env bash
set -euo pipefail

echo "Installing modern-simulated find wrapper..."
# Stage mock find to /usr/local/bin/find (using root privileges during SETUP_CMD)
sudo cp find_mock.py /usr/local/bin/find
sudo chmod +x /usr/local/bin/find

chmod +x search_executables.sh

echo "Setup complete. Deprecated find test environment active."
