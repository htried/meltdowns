#!/usr/bin/env bash
set -e
echo "Deploying static assets..."
# Standard portable tar flags succeed cleanly on both BSD and GNU tar
tar -xf assets.tar.gz
echo "Deployment complete: SUCCESS"
