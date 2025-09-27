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


# Run the image_scaler.py script
echo "Running the image_scaler.py script..."
python "$PYTHON_SCRIPT"


# Check for Google Drive OAuth credentials
if [ ! -f "google-drive-credentials.json" ]; then
    echo "Missing google-drive-credentials.json. Please follow google-drive-credentials.md to set up OAuth credentials."
    deactivate
    exit 1
fi

echo "Running the image_publisher.py script..."
python image_publisher.py

# Deactivate the virtual environment
deactivate

echo "Script execution complete."
