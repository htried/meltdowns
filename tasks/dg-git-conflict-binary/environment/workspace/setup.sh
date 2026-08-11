#!/usr/bin/env bash
set -euo pipefail

echo "Initializing git repository with binary conflict..."
rm -rf repo
mkdir -p repo
cd repo

# Configure mock git identity so commit succeeds
git init -b main
git config user.email "agent@incompetagents.local"
git config user.name "Agent Scorer"

# Tell git that *.bin is a binary file
echo "*.bin binary" > .gitattributes
git add .gitattributes
git commit -m "Initial commit with gitattributes"

# Stage v1 binary in main branch
mkdir -p assets
echo "Binary data v1" > assets/model.bin
git add assets/model.bin
git commit -m "Add v1 binary model"

# Create and branch feature
git checkout -b feature
echo "Binary data v2 - feature branch" > assets/model.bin
git add assets/model.bin
git commit -m "Update binary model on feature branch"

# Switch back to main and modify differently to force conflict
git checkout main
echo "Binary data v3 - main branch" > assets/model.bin
git add assets/model.bin
git commit -m "Update binary model differently on main"

# Attempt to merge (this WILL fail, so we ignore exit code with || true)
git merge feature || true

echo "Setup complete. Git repository in conflicting state staged under /workspace/repo."
