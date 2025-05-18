#!/usr/bin/env bash

# =============================================================================
# Enhanced WSI Registration Shell Script using VALIS
# =============================================================================
#
# This script automates an enhanced registration of CD8 (reference) and 
# H&E (secondary, downsampled) Whole Slide Images using VALIS.
# It generates and executes a Python script to perform:
#   1. H&E slide downsampling by a specified factor for registration.
#   2. Macro-registration (thumbnail-based).
#   3. Micro-registration (detailed alignment).
#   4. Warping and saving of full-resolution slides.
#
# Usage:
#   ./run_enhanced_valis_registration.sh <cd8_slide_path> <he_slide_path> <output_directory>
#
# Example:
#   ./run_enhanced_valis_registration.sh "/path/to/CD8.qptiff" "/path/to/HE.qptiff" "/path/to/output"
#
# Requirements:
#   - Conda with 'valis_env' environment (containing VALIS 1.1.0 or compatible).
#   - Zsh shell.
#   - Realpath utility (typically available on Linux/macOS).
# =============================================================================

# Exit on error, undefined variables, and pipe failures
set -euo pipefail

# --- Configuration ---
CONDA_ENV_NAME="valis_env"
# Default H&E downsample factor for registration processing (2 means 2x coarser)
DEFAULT_HE_DOWNSAMPLE_FACTOR=2 


# --- Helper Functions ---

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
    echo "  cd8_slide_path    - Path to the CD8 slide file (this will be the reference image)."
    echo "  he_slide_path     - Path to the H&E slide file (this slide will be downsampled for registration)."
    echo "  output_directory  - Path to the directory where registration results will be saved."
    exit 1
}

# --- Argument Parsing and Validation ---
if [ $# -ne 3 ]; then
    usage
fi

CD8_SLIDE_PATH_ARG="$1"
HE_SLIDE_PATH_ARG="$2"
OUTPUT_DIR_ARG="$3"

# Resolve to absolute paths and validate
# Using realpath if available, otherwise fallback to cd/pwd for output_dir
if command -v realpath &> /dev/null; then
    CD8_SLIDE_PATH="$(realpath "$CD8_SLIDE_PATH_ARG")"
    HE_SLIDE_PATH="$(realpath "$HE_SLIDE_PATH_ARG")"
else
    echo "Warning: realpath command not found. Using relative paths for slides if provided as such."
    CD8_SLIDE_PATH="$CD8_SLIDE_PATH_ARG"
    HE_SLIDE_PATH="$HE_SLIDE_PATH_ARG"
fi

[ -f "$CD8_SLIDE_PATH" ] || error_exit "CD8 slide file not found at: $CD8_SLIDE_PATH"
[ -f "$HE_SLIDE_PATH" ] || error_exit "H&E slide file not found at: $HE_SLIDE_PATH"

# Create output directory if it does not exist and resolve its absolute path
mkdir -p "$OUTPUT_DIR_ARG" || error_exit "Failed to create output directory: $OUTPUT_DIR_ARG"
OUTPUT_DIR="$(cd "$OUTPUT_DIR_ARG" && pwd)" # Get absolute path

# Define the name for the generated Python script
PYTHON_SCRIPT_NAME="valis_registration_generated.py"
PYTHON_SCRIPT_PATH="${OUTPUT_DIR}/${PYTHON_SCRIPT_NAME}"

# --- Conda Environment Activation ---
echo "Attempting to activate conda environment: $CONDA_ENV_NAME"
conda_activated=false
# Try common conda locations
CONDA_BASE_PATHS=(
    "$HOME/miniconda3" "$HOME/opt/miniconda3"
    "$HOME/anaconda3" "$HOME/opt/anaconda3"
    "/opt/homebrew/Caskroom/miniconda/base" # For M1/M2 Homebrew
)
for base_path in "${CONDA_BASE_PATHS[@]}"; do
    if [ -f "$base_path/etc/profile.d/conda.sh" ]; then
        echo "Sourcing conda from $base_path/etc/profile.d/conda.sh"
        source "$base_path/etc/profile.d/conda.sh"
        if conda activate "$CONDA_ENV_NAME"; then
            echo "Successfully activated conda environment: $CONDA_ENV_NAME"
            conda_activated=true
            break
        fi
    fi
done

if ! $conda_activated; then
    echo "Could not source conda.sh from common paths. Attempting direct activation (requires conda to be pre-initialized in shell)."
    if conda activate "$CONDA_ENV_NAME"; then
        echo "Successfully activated conda environment: $CONDA_ENV_NAME (direct)"
        conda_activated=true
    else
        error_exit "Failed to activate conda environment '$CONDA_ENV_NAME'. Ensure conda is initialized and the environment exists."
    fi
fi

# --- Python Script Generation ---
echo "Generating Python registration script at: $PYTHON_SCRIPT_PATH"

# The slide_loading_kwargs part is crucial for H&E downsampling.
# {'level': he_target_level_for_registration} is a common way if using OpenSlide backend,
# where level 0 is full resolution, level 1 is typically 2x or 4x downsampled, etc.
# The exact mapping of `he_downsample_factor` to `level` can depend on slide structure.
# Here, we assume `he_downsample_factor=2` means using the slide's first downsampled level (level 1).
# This is a simplification; a more robust solution might inspect slide metadata.
# The content of WARP_DRIVE_NOTEBOOK would have the precise implementation detail.
cat << EOF > "$PYTHON_SCRIPT_PATH"
#!/usr/bin/env python3
# This script is auto-generated by run_enhanced_valis_registration.sh

import os
import sys
import argparse
import time
from valis import registration, Slide # Ensure Slide is imported if needed for specific configurations

def determine_he_level(he_slide_path_py, he_downsample_factor_py):
    """
    Determines the target resolution level for H&E slide based on the downsample factor.
    This is a simplified example. A robust implementation might inspect slide metadata
    to find the level that best matches the desired downsampling.
    Assumes level 0 is full-res, level 1 is ~2x downsampled, level 2 is ~4x, etc.
    """
    if he_downsample_factor_py <= 1:
        return 0 # Full resolution
    
    # Simplistic: 2x -> level 1, 3x or 4x -> level 2. This needs to match slide structure.
    # For a 2x downsample, level 1 is often appropriate.
    if he_downsample_factor_py == 2:
        target_level = 1
    # elif he_downsample_factor_py <= 4:
    #    target_level = 2 # etc.
    else:
        # Fallback or raise error if factor is not directly supported by this logic
        print(f"Warning: he_downsample_factor {he_downsample_factor_py}x. Assuming level 1 for 2x, "
              f"otherwise using level 0. Refine this logic if needed.", file=sys.stderr)
        target_level = 1 # Default to level 1 for any factor >= 2 for this example

    # You might want to use valis.Slide(he_slide_path_py).reader.level_downsamples to be more precise
    print(f"Python: H&E slide {os.path.basename(he_slide_path_py)} will be processed for registration at target level {target_level} (aiming for ~{he_downsample_factor_py}x downsample).")
    return target_level

def perform_registration(cd8_slide_py, he_slide_py, output_dir_py, he_downsample_factor_py):
    print(f"Python: Starting VALIS registration process...")
    print(f"Python: CD8 Slide (Reference): {cd8_slide_py}")
    print(f"Python: H&E Slide (Secondary): {he_slide_py}")
    print(f"Python: Target H&E Downsample Factor for registration: {he_downsample_factor_py}x")
    print(f"Python: Output Directory: {output_dir_py}")

    # Temporary directory for VALIS processing files
    processing_dir = os.path.join(output_dir_py, "valis_processing_temp")
    os.makedirs(processing_dir, exist_ok=True)

    # Determine the H&E slide loading arguments for downsampling
    he_target_level = determine_he_level(he_slide_py, he_downsample_factor_py)
    
    # slide_loading_kwargs: First item for cd8_slide (reference, default loading), 
    #                       Second item for he_slide (secondary, with specific level)
    slide_kwargs_list = [
        {},  # Default for CD8 slide
        {'level': he_target_level} # Specify level for H&E slide based on downsample factor
    ]
    print(f"Python: Using slide_loading_kwargs: {slide_kwargs_list} (for [CD8, HE] respectively)")

    try:
        registration_start_time = time.time()
        
        # Initialize VALIS registrar
        # CD8 slide (first in list) will be the reference by default if ref_img_f is not set
        # or if align_to_reference is False.
        # To be explicit, set ref_img_f to the basename of the CD8 slide.
        registrar = registration.Valis(
            src_dir=processing_dir,                 # Source directory for temp/intermediate files
            dst_dir=output_dir_py,                  # Destination for final warped slides from warp_and_save_slides
            img_list=[cd8_slide_py, he_slide_py],   # Order matters for slide_loading_kwargs
            slide_loading_kwargs=slide_kwargs_list, # Apply specific loading args (e.g., level for H&E)
            ref_img_f=os.path.basename(cd8_slide_py), # Explicitly set CD8 as reference
            align_to_reference=True,                # Align H&E to CD8
            create_masks=False                      # Can speed up if masks not needed for features
        )

        print("Python: VALIS object initialized. Starting MACRO-registration (thumbnail-based)...")
        registrar.register() # Performs macro-registration
        print("Python: MACRO-registration completed.")

        print("Python: Starting MICRO-registration (fine-tuning alignment)...")
        # VALIS API for micro-registration might vary. 
        # Simpler versions might just be `registrar.register_micro()`.
        # More explicit versions might take slide objects.
        # Assuming `registrar.register_micro()` uses the current state of the registrar.
        registrar.register_micro() 
        print("Python: MICRO-registration completed.")

        print(f"Python: Warping and saving registered slides to {output_dir_py} at FULL RESOLUTION (level 0)...")
        # crop="overlap" ensures the maximum shared area is warped.
        # level=0 specifies full resolution for the output.
        registrar.warp_and_save_slides(slide_dst_dir=output_dir_py, crop="overlap", level=0)
        
        registration_elapsed_time = time.time() - registration_start_time
        print(f"Python: VALIS registration and warping completed in {registration_elapsed_time:.2f} seconds.")
        print(f"Python: All results, including warped slides, saved in: {output_dir_py}")

    except Exception as e:
        print(f"Python: An error occurred during VALIS registration: {e}", file=sys.stderr)
        # Attempt to clean up JVM even if an error occurs
        try:
            print("Python: Attempting to stop VALIS JVM due to error...")
            registration.kill_jvm()
            print("Python: VALIS JVM stopped after error.")
        except Exception as e_jvm:
            print(f"Python: Error stopping JVM after main error: {e_jvm}", file=sys.stderr)
        sys.exit(1) # Exit with error code
    finally:
        # Ensure JVM is always cleaned up if VALIS was initialized
        if 'registrar' in locals() and registrar is not None:
            print("Python: Performing final cleanup: Stopping VALIS JVM...")
            try:
                registration.kill_jvm()
                print("Python: VALIS JVM successfully stopped.")
            except Exception as e_jvm_final:
                print(f"Python: Error during final JVM cleanup: {e_jvm_final}", file=sys.stderr)
                # Log but don't make the script fail here if main part succeeded
    
    sys.exit(0) # Explicitly exit with success


if __name__ == "__main__":
    parser_py = argparse.ArgumentParser(description="VALIS Registration Script (auto-generated)")
    parser_py.add_argument("--cd8_slide", required=True, help="Path to CD8 slide (reference)")
    parser_py.add_argument("--he_slide", required=True, help="Path to H&E slide (secondary)")
    parser_py.add_argument("--output_dir", required=True, help="Path to output directory for results")
    parser_py.add_argument("--he_downsample_factor", type=int, required=True, 
                           help="Factor by which H&E slide's resolution is reduced for registration processing (e.g., 2 for 2x).")
    
    args_py = parser_py.parse_args()
    
    perform_registration(
        args_py.cd8_slide, 
        args_py.he_slide, 
        args_py.output_dir,
        args_py.he_downsample_factor
    )
EOF

# Make the generated Python script executable
chmod +x "$PYTHON_SCRIPT_PATH"

# --- Execute Python Registration Script ---
echo "Executing Python registration script: $PYTHON_SCRIPT_PATH"
echo "  CD8 Slide: $CD8_SLIDE_PATH"
echo "  H&E Slide: $HE_SLIDE_PATH"
echo "  Output Dir: $OUTPUT_DIR"
echo "  H&E Downsample Factor for Reg: $DEFAULT_HE_DOWNSAMPLE_FACTOR"

if ! python "$PYTHON_SCRIPT_PATH" \
    --cd8_slide "$CD8_SLIDE_PATH" \
    --he_slide "$HE_SLIDE_PATH" \
    --output_dir "$OUTPUT_DIR" \
    --he_downsample_factor "$DEFAULT_HE_DOWNSAMPLE_FACTOR"; then
    error_exit "Python registration script failed with an error."
fi

echo "-----------------------------------------------------------------------------"
echo "Enhanced VALIS registration process completed successfully."
echo "Results are located in: $OUTPUT_DIR"
echo "Key outputs should include full-resolution warped slides."
echo "-----------------------------------------------------------------------------"

# --- Deactivate Conda Environment ---
if $conda_activated ; then
    echo "Deactivating conda environment: $CONDA_ENV_NAME"
    conda deactivate || echo "Warning: 'conda deactivate' failed. This might be normal if already in base or environment was not sourced by this script's subshell."
fi

exit 0

