#!/bin/bash

# Define variables
VENV_DIR="venv"
PYTHON_SCRIPT="image_scaler.py"

# Activate the virtual environment
source "$VENV_DIR/bin/activate"

# Run the image_scaler.py script
echo "Running the image_scaler.py script..."
python "$PYTHON_SCRIPT"

# Deactivate the virtual environment
deactivate

echo "Script execution complete."
