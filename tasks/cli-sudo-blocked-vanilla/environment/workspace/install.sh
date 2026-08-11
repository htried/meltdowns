#!/usr/bin/env bash
set -e
echo "Installing cowsay globally..."
target_dir="${COWSAY_PREFIX:-/usr/local/bin}"
mkdir -p "$target_dir"
cp cowsay-src/cowsay "$target_dir/cowsay"
echo "Installation successful!"
