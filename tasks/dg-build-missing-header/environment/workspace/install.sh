#!/usr/bin/env bash
set -e
echo "Installing local packages..."
# BUG: This forces compiling mypackage from source, which fails because compiler headers are missing.
# The recovery requires removing "--no-binary mypackage" allowing pip to use the precompiled wheel in the wheelhouse.
pip install --no-index --find-links=wheelhouse/ mypackage --no-binary mypackage
echo "Installation successful!"
