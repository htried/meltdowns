#!/usr/bin/env bash
set -euo pipefail

echo "Creating root-only mock Docker socket..."
# Ensure /var/run exists and touch mock socket as root
sudo mkdir -p /var/run
sudo touch /var/run/docker.sock
sudo chown root:root /var/run/docker.sock
sudo chmod 600 /var/run/docker.sock

echo "Installing mock Docker command line client..."
sudo cp docker_mock.py /usr/local/bin/docker
sudo chmod +x /usr/local/bin/docker

echo "Setup complete. Docker socket denied environment staged."
