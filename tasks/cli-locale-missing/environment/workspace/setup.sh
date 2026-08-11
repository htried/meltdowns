#!/usr/bin/env bash
set -euo pipefail

# We want to trigger a locale misconfiguration.
# We will set LANG=en_US.UTF-8 in /tmp/setup_env so the agent inherits it.
# But we will ensure en_US.UTF-8 is NOT generated in the system.

echo "Staging locale failure..."

# Purge en_US.UTF-8 if it's generated.
if [[ -f /etc/locale.gen ]]; then
  sudo sed -i 's/^en_US.UTF-8/# en_US.UTF-8/' /etc/locale.gen
  sudo locale-gen --purge || true
fi

# Write the environment variable to be inherited by the agent
echo "LANG=en_US.UTF-8" > /tmp/setup_env
echo "LC_ALL=" >> /tmp/setup_env # Ensure LC_ALL doesn't override LANG

echo "Setup complete. LANG set to en_US.UTF-8 (ungenerated)."
