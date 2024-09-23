#!/bin/bash

# Exit the script if any command fails
set -e

# Build the Python package
echo "Building the Python package..."
cd server/
python3.11 -m build --wheel

# Install the built package
echo "Installing the package..."
pip install dist/qview3dserver-1.0.0-py3-none-any.whl

echo "Build and installation completed successfully."