#!/usr/bin/env bash
# =============================================================================
# RNV Text Transformer - Linux/macOS Build Script
# =============================================================================
# Builds a standalone distribution using PyInstaller and the bundled
# RNV_Text_Transformer.spec file.
#
# Output: dist/RNV Text Transformer/RNV Text Transformer
# =============================================================================

set -e
cd "$(dirname "$0")"

echo
echo "============================================================================"
echo "  RNV Text Transformer - Build (Linux/macOS)"
echo "============================================================================"
echo

# ── Step 1: Activate venv if present ────────────────────────────────────────
if [ -f ".venv/bin/activate" ]; then
    echo "[1/5] Activating virtual environment..."
    # shellcheck disable=SC1091
    source .venv/bin/activate
else
    echo "[1/5] No .venv found - using system Python"
fi

# ── Step 2: Verify PyInstaller is installed ─────────────────────────────────
echo "[2/5] Checking PyInstaller installation..."
if ! python -c "import PyInstaller" 2>/dev/null; then
    echo
    echo "ERROR: PyInstaller is not installed."
    echo
    echo "Install it with:"
    echo "    pip install pyinstaller"
    echo
    exit 1
fi

# ── Step 3: Clean previous build artifacts ──────────────────────────────────
echo "[3/5] Cleaning previous build artifacts..."
rm -rf build dist

# ── Step 4: Run PyInstaller ─────────────────────────────────────────────────
echo "[4/5] Running PyInstaller..."
echo
if ! pyinstaller --noconfirm RNV_Text_Transformer.spec; then
    echo
    echo "============================================================================"
    echo "  BUILD FAILED"
    echo "============================================================================"
    echo
    exit 1
fi

# ── Step 5: Report output location ──────────────────────────────────────────
echo
echo "[5/5] Build complete!"
echo
echo "============================================================================"
echo "  BUILD SUCCEEDED"
echo "============================================================================"
echo
echo "Output location:"
echo "    dist/RNV Text Transformer/RNV Text Transformer"
echo
echo "To run the built application:"
echo "    './dist/RNV Text Transformer/RNV Text Transformer'"
echo
echo "To create a tarball or zip, package the entire folder:"
echo "    dist/RNV Text Transformer/"
echo
