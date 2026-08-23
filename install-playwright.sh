#!/bin/bash

# Script para instalar Playwright e browsers
# Execute após: pip install -r requirements.txt

echo "Installing Playwright..."
pip install playwright>=1.40.0

echo "Installing Chromium browser..."
playwright install chromium

echo "Installing Firefox browser (opcional)..."
playwright install firefox

echo "Installing WebKit browser (opcional)..."
playwright install webkit

echo ""
echo "✅ Playwright installation complete!"
echo ""
echo "You can now use human_challenge.py to resolve drc|1402 challenges"
echo ""
echo "Verify installation:"
echo "  python -c \"from playwright.async_api import async_playwright; print('✅ Playwright ready')\""
