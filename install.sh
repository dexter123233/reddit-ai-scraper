#!/bin/bash
# Reddit AI Scraper - Quick Start
# Run: bash <(curl -sSL https://raw.githubusercontent.com/dexter123233/reddit-ai-scraper/main/install.sh)

set -e

echo "Cloning Reddit AI Scraper..."
TMP_DIR="/tmp/reddit-scraper-$$"
rm -rf "$TMP_DIR"
git clone --depth 1 https://github.com/dexter123233/reddit-ai-scraper.git "$TMP_DIR" 2>/dev/null || {
    echo "Cloning from current directory..."
    TMP_DIR="$(cd "$(dirname "$0")" && pwd)"
}

cd "$TMP_DIR"

echo ""
echo "========================================"
echo "Reddit AI Scraper"
echo "========================================"
echo ""
echo "Starting server on http://localhost:8080"
echo ""

# Try to open browser
xdg-open http://localhost:8080 2>/dev/null || open http://localhost:8080 2>/dev/null || true

exec python3 server.py
