# WSI Slide Registration Tool

This repository contains scripts for performing slide registration on Whole Slide Images (WSI) using the VALIS (Version 1.1.0) registration framework. It's specifically designed to co-register H&E and CD8 stained slides.

## Contents

- `wsi_registration.sh`: Main shell script that handles environment setup and coordinates the registration process
- `slide_registration.py`: Python script that performs the actual slide registration using VALIS
- `environment.yml`: Conda environment specification with all required dependencies

## Requirements

- Conda or Miniconda installed
- All dependencies are specified in the `environment.yml` file

## Setup

### Creating the Conda Environment

```bash
# Create and activate the conda environment from the environment.yml file
conda env create -f environment.yml
conda activate valis_env
```

## Usage

### Basic Usage

```bash
./wsi_registration.sh <cd8_slide_path> <he_slide_path> <output_directory>
```

### Example

```bash
./wsi_registration.sh "/path/to/CD8.qptiff" "/path/to/HE.qptiff" "/path/to/output"
```

## Output

The registration process will create the following in your output directory:

- `registration_results/`: Directory containing the registered slides
- `registration_evaluation/`: Directory containing evaluation metrics

## How It Works

1. The shell script (`wsi_registration.sh`):
   - Activates the conda environment
   - Validates input files
   - Creates necessary directories
   - Calls the Python registration script
   - Verifies successful completion

2. The Python script (`slide_registration.py`):
   - Initializes VALIS with the appropriate parameters
   - Performs the actual registration
   - Warps and saves the aligned slides
   - Cleans up resources

## Dependencies

The project relies on the following key dependencies, specified in `environment.yml`:
- VALIS 1.1.0 (via PyPI package valis-wsi)
- Python 3.10
- OpenJDK 11+ (for Bio-Formats)
- Maven (for Bio-Formats)
- OpenSlide and Python bindings
- PyVips
- Various Python libraries (scikit-image, numpy, etc.)

## Notes

- This workflow is specifically tailored for H&E and CD8 WSI registration
- Error handling is built in to help diagnose issues
- The conda environment ensures reproducibility across different systems

## Troubleshooting

If you encounter issues:

1. Ensure your conda environment is properly created and activated:
   ```bash
   conda env create -f environment.yml
   conda activate valis_env
   ```
2. Verify the input slide paths are correct and accessible
3. Check that you have permissions to write to the output directory
4. Review output messages for specific error information
