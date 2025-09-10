#!/bin/bash

# OpenBao Replication Setup Script
# This script helps set up the Python environment and dependencies

set -e

echo "Setting up OpenBao Replication Tool..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed"
    exit 1
fi

# Check Python version (requires 3.7+)
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.7"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python 3.7+ is required, but found Python $python_version"
    exit 1
fi

echo "Found Python $python_version ✓"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Virtual environment created ✓"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo "Setup completed successfully! ✓"
echo ""
echo "To use the replication tool:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Copy and edit the config file: cp config.yaml my-config.yaml"
echo "3. Run the tool: python openbao_replication.py --config my-config.yaml --action health"
echo ""
echo "For help: python openbao_replication.py --help"
