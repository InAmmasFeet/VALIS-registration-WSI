#!/usr/bin/env python3
"""
Slide Registration Script
=========================

This script performs slide registration using VALIS 1.1.0.
It registers and aligns HE and CD8 whole slide images.

Usage:
    python slide_registration.py --cd8_slide <cd8_path> --he_slide <he_path> --output_dir <output_path>

Requirements:
    - VALIS 1.1.0
    - Python 3.7+

Author: Generated script for slide co-registration
Date: Generated at runtime using datetime.date.today().isoformat()
"""

import os
import sys
import time
import argparse
from datetime import date
from valis import registration

DATE_STR = date.today().isoformat()

def main():
    parser = argparse.ArgumentParser(description="Perform slide registration with VALIS")
    parser.add_argument("--cd8_slide", required=True, help="Path to CD8 slide")
    parser.add_argument("--he_slide", required=True, help="Path to H&E slide")
    parser.add_argument("--output_dir", required=True, help="Path to output directory")
    args = parser.parse_args()

    cd8_slide = args.cd8_slide
    he_slide = args.he_slide
    output_dir = args.output_dir

    # Validate paths
    if not os.path.exists(cd8_slide):
        print(f"Error: CD8 slide not found at {cd8_slide}")
        sys.exit(1)
    if not os.path.exists(he_slide):
        print(f"Error: H&E slide not found at {he_slide}")
        sys.exit(1)
    if not os.path.exists(output_dir):
        print(f"Creating output directory: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)

    print("Starting registration process...")
    start_time = time.time()

    # Create the slide paths
    slide_paths = [cd8_slide, he_slide]

    # Initialize VALIS
    registrar = registration.Valis(
        src_dir=output_dir,      # Source directory
        dst_dir=output_dir,      # Destination directory
        img_list=slide_paths,    # List of slide paths
        max_image_dim_px=1024    # Default max image dimension in pixels
    )

    # Perform registration
    registrar.register()

    # Warp and save the registered slides to the output directory
    print(f"Warping and saving aligned slides to: {output_dir}")
    registrar.warp_and_save_slides(output_dir, crop="overlap")
    
    # Clean up the JVM as recommended
    print("Cleaning up resources...")
    registration.kill_jvm()
    
    elapsed_time = time.time() - start_time
    print(f"Registration completed in {elapsed_time:.2f} seconds")
    print(f"Results saved to: {output_dir}")
    
    # Return success status for shell script
    return 0

if __name__ == "__main__":
    sys.exit(main())
