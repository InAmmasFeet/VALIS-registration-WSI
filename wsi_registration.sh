#!/bin/bash
# =============================================================================
# WSI Registration Shell Script
# =============================================================================
#
# This script automates the registration of HE and CD8 Whole Slide Images using VALIS.
# It activates the required conda environment and runs the Python registration script.
#
# Usage:
#   ./wsi_registration.sh <cd8_slide_path> <he_slide_path> <output_directory>
#
# Example:
#   ./wsi_registration.sh "/path/to/CD8.qptiff" "/path/to/HE.qptiff" "/path/to/output"
#
# Requirements:
#   - Conda with valis_env environment containing VALIS 1.1.0
#   - Python 3.7+ with necessary packages installed in the valis_env
#   - slide_registration.py script in the same directory
#
# Author: Generated script for slide co-registration
# Date: $(date +%Y-%m-%d)
# =============================================================================

# Exit on error, undefined variables, and pipe failures
set -euo pipefail

# Function to display error messages and exit
error_exit() {
    echo "ERROR: $1" >&2
    exit 1
}

# Function to display usage information
usage() {
    echo "Usage: $0 <cd8_slide_path> <he_slide_path> <output_directory>"
    echo
    echo "Arguments:"
    echo "  cd8_slide_path    - Path to the CD8 slide file"
    echo "  he_slide_path     - Path to the HE slide file"
    echo "  output_directory  - Path to the output directory for registration results"
    exit 1
}

# Check if correct number of arguments
if [ $# -ne 3 ]; then
    usage
fi

# Assign arguments to variables
CD8_SLIDE="$1"
HE_SLIDE="$2"
OUTPUT_DIR="$3"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/slide_registration.py"

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    error_exit "Python registration script not found at: $PYTHON_SCRIPT"
fi

# Check if files exist
[ -f "$CD8_SLIDE" ] || error_exit "CD8 slide file not found at: $CD8_SLIDE"
[ -f "$HE_SLIDE" ] || error_exit "HE slide file not found at: $HE_SLIDE"

# Create output directory if it does not exist
mkdir -p "$OUTPUT_DIR" || error_exit "Failed to create output directory: $OUTPUT_DIR"

# Activate conda environment
echo "Activating valis_env conda environment..."

# Ensure the `conda` command is available. If not, try sourcing common initialization scripts
if ! command -v conda >/dev/null 2>&1; then
    if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
        source "$HOME/miniconda3/etc/profile.d/conda.sh"
    elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
        source "$HOME/anaconda3/etc/profile.d/conda.sh"
    else
        error_exit "conda command not found. Please ensure conda is installed and in your PATH."
    fi
fi

# Initialize conda for this shell and activate the environment
eval "$(conda shell.bash hook)" >/dev/null 2>&1
conda activate valis_env || error_exit "Failed to activate valis_env conda environment. Please ensure it exists."

echo "Starting slide registration process..."
echo "CD8 Slide: $CD8_SLIDE"
echo "HE Slide: $HE_SLIDE"
echo "Output Directory: $OUTPUT_DIR"

# Run the registration script
echo "Executing VALIS registration..."
if ! python "$PYTHON_SCRIPT" --cd8_slide "$CD8_SLIDE" --he_slide "$HE_SLIDE" --output_dir "$OUTPUT_DIR"; then
    error_exit "Registration process failed with an error."
fi

# Create evaluation directory
EVAL_DIR="$OUTPUT_DIR/registration_evaluation"
mkdir -p "$EVAL_DIR"

# Check for success
if [ -d "$OUTPUT_DIR/registration_results" ]; then
    echo "Registration completed successfully!"
    echo "Results are available in: $OUTPUT_DIR"

    # Deactivate conda environment
    conda deactivate

    exit 0
else
    error_exit "Registration process did not complete successfully."
fi
