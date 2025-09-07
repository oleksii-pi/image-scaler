#!/bin/bash

# Define variables
VENV_DIR="venv"
PYTHON_SCRIPT="image_scaler.py"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install it and try again."
    exit 1
fi

# Set up the virtual environment if not already present
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "Virtual environment created."
fi

# Activate the virtual environment
source "$VENV_DIR/bin/activate"

# Install required packages
echo "Installing required Python packages..."
pip install --upgrade pip
pip install -r requirements.txt
echo "Packages installed."

# Run the Python script
echo "Running the Python script..."
python "$PYTHON_SCRIPT"

# Deactivate the virtual environment
deactivate

echo "Script execution complete."
