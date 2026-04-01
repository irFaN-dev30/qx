#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# 1. Install Python dependencies
# Vercel's Python runtime automatically does this, but we specify it for clarity.
echo "Installing Python dependencies..."
pip install --disable-pip-version-check --no-cache-dir -r functions/signal_function/requirements.txt

# 2. Install Playwright browsers and their OS dependencies
# This is the crucial step to fix the 500 error.
echo "Installing Playwright browsers and dependencies..."
playwright install --with-deps chromium

# 3. (Optional) Run Next.js build for the dashboard
# This ensures your frontend is also built correctly.
echo "Building Next.js dashboard..."
(cd dashboard && npm install && npm run build)

echo "Vercel build script completed successfully!"
