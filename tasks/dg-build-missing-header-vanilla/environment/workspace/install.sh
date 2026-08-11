#!/usr/bin/env bash
set -e
echo "Installing local packages..."
# Standard pip install parses local find-links and resolves the precompiled staged wheel cleanly
pip install --no-index --find-links=wheelhouse/ mypackage
echo "Installation successful!"
