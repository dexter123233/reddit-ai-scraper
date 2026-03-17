#!/bin/bash
# Reddit AI Scraper - One Command
# Run: curl -sSL https://raw.githubusercontent.com/dexter123233/reddit-ai-scraper/main/install.sh | bash

set -e

TMP_DIR="/tmp/reddit-scraper-$$"
rm -rf "$TMP_DIR"
git clone --depth 1 https://github.com/dexter123233/reddit-ai-scraper.git "$TMP_DIR"

echo ""
echo "╔══════════════════════════════════════╗"
echo "║   🤖 REDDIT AI SCRAPER             ║"
echo "║   Pain Point Radar v2.0            ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "🌐 Open: http://localhost:8080"
echo ""

cd "$TMP_DIR"
python3 server.py
