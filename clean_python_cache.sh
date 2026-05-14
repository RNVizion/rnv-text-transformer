#!/usr/bin/env bash
# RNV Text Transformer - Python Cache Cleaner
# Removes all __pycache__ directories and .pyc files

set -u

echo "================================"
echo "RNV Text Transformer Cache Cleaner"
echo "================================"
echo

# Resolve script directory so it cleans the project root regardless of CWD
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

echo "Removing __pycache__ directories..."
find . -type d -name "__pycache__" -print -exec rm -rf {} +

echo
echo "Removing .pyc files..."
find . -type f -name "*.pyc" -print -delete

echo
echo "================================"
echo "Cache cleanup complete!"
echo "================================"
