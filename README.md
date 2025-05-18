# WSI Slide Registration Tool

This repository contains scripts for performing slide registration on Whole Slide Images (WSI) using the VALIS (Version 1.1.0) registration framework. It's specifically designed to co-register H&E and CD8 stained slides.

## Contents

- `wsi_registration.sh`: Main shell script that handles environment setup and coordinates the registration process
- `slide_registration.py`: Python script that performs the actual slide registration using VALIS
- `run_enhanced_valis_registration.sh`: Bash script that generates and runs a Python program for more advanced VALIS options
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

### Enhanced Workflow

For more advanced registration features, use `run_enhanced_valis_registration.sh`. This
script automatically generates a Python program that performs H&E downsampling,
macro- and micro-registration, and then saves full‑resolution warped slides.

```bash
./run_enhanced_valis_registration.sh <cd8_slide_path> <he_slide_path> <output_directory>
```

This script requires the `bash` shell and the `valis_env` conda environment to be available.

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
3. The enhanced shell script (`run_enhanced_valis_registration.sh`):
   - Generates a dedicated Python script at run time
   - Downsamples the H&E slide for faster processing
   - Executes both macro- and micro-registration steps
   - Warps and saves slides at full resolution

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

## Running on Harvard O2

When using the O2 cluster, load the necessary modules and activate the conda
environment before executing a script. A typical setup is:

```bash
module load Anaconda3
module load openjdk/11.0.2
module load maven
conda activate valis_env
```

Once the environment is active you can run either `wsi_registration.sh` or the
enhanced `run_enhanced_valis_registration.sh` just as on a local machine.

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
