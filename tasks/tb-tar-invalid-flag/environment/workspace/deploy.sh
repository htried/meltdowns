#!/usr/bin/env bash
set -e
echo "Deploying static assets..."
# This uses GNU specific flags --overwrite and --exclude-vcs which fail on BSD tar
tar --overwrite --exclude-vcs -xf assets.tar.gz
echo "Deployment complete!"
