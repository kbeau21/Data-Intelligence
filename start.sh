#!/bin/bash

echo ""
echo "  ============================================"
echo "   Company Intelligence System - Starting..."
echo "  ============================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "  Python 3 is not installed on this computer."
    echo ""
    echo "  To install:"
    echo "    Mac:   brew install python3"
    echo "    Linux: sudo apt install python3 python3-pip"
    echo ""
    echo "  Or download from: https://www.python.org/downloads/"
    echo ""
    exit 1
fi

# Install dependencies
echo "  Installing required packages (first time only)..."
pip3 install -q -r requirements.txt 2>/dev/null || pip3 install flask pandas openpyxl requests python-dotenv 2>/dev/null
echo "  Done."
echo ""

# Open browser (works on Mac and Linux)
echo "  Opening your browser..."
sleep 2
if [[ "$OSTYPE" == "darwin"* ]]; then
    open http://localhost:5000
else
    xdg-open http://localhost:5000 2>/dev/null || echo "  Open http://localhost:5000 in your browser"
fi

echo ""
echo "  ============================================"
echo "   App is running at: http://localhost:5000"
echo "   Upload your Excel file in the browser."
echo ""
echo "   To stop: close this window or press Ctrl+C"
echo "  ============================================"
echo ""
python3 app.py
