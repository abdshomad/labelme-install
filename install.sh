#!/bin/bash

# install.sh - Install labelme using uv venv
# Uses existing venv if it exists, otherwise creates a new one

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"

echo "=========================================="
echo "Labelme Installation Script"
echo "=========================================="

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed. Please install uv first."
    echo "Visit: https://github.com/astral-sh/uv"
    exit 1
fi

# Check if venv exists
if [ -d "$VENV_DIR" ]; then
    echo "✓ Virtual environment already exists at: $VENV_DIR"
    echo "  Using existing virtual environment..."
else
    echo "Creating new virtual environment..."
    cd "$SCRIPT_DIR"
    uv venv
    echo "✓ Virtual environment created at: $VENV_DIR"
fi

# Activate venv and install dependencies
echo ""
echo "Installing dependencies..."
cd "$SCRIPT_DIR"
source "$VENV_DIR/bin/activate"

# Sync dependencies using uv
uv sync --dev

# Install the package in editable mode to ensure it's properly compiled/installed
echo ""
echo "Installing labelme package in editable mode..."
uv pip install -e .

echo ""
echo "=========================================="
echo "✓ Installation completed successfully!"
echo "=========================================="
echo ""
echo "To activate the virtual environment, run:"
echo "  source $VENV_DIR/bin/activate"
echo ""
echo "To run labelme, use:"
echo "  ./run.sh"
echo "  or"
echo "  source .venv/bin/activate && labelme"
echo ""

