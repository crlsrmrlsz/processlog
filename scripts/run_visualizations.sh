#!/bin/bash
#
# Wrapper script to run visualization generation with proper environment
#

set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

# Check if Graphviz is installed
if ! command -v dot &> /dev/null; then
    echo "ERROR: Graphviz is not installed"
    echo ""
    echo "PM4Py visualizations require the Graphviz system package."
    echo ""
    echo "Install on Ubuntu/Debian:"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install graphviz"
    echo ""
    echo "Install on macOS:"
    echo "  brew install graphviz"
    echo ""
    echo "After installation, verify with: dot -V"
    echo ""
    echo "See scripts/README.md for more information."
    exit 1
fi

# Check if virtual environment exists
VENV_DIR="$PROJECT_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "ERROR: Virtual environment not found at $VENV_DIR"
    echo "Please run: python3 -m venv venv && source venv/bin/activate && pip install -e ."
    exit 1
fi

# Activate virtual environment and run script
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "Running visualization generator..."
python3 "$SCRIPT_DIR/generate_visualizations.py"

echo ""
echo "SUCCESS! Visualizations saved to visualizations/ folder"
