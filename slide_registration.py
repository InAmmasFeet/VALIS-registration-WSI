#!/usr/bin/env python3
"""
Slide Registration Script
=========================

This script performs slide registration using VALIS 1.1.0.
It registers and aligns HE and CD8 whole slide images, saving results
to a ``registration_results`` directory within the specified output path.

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
from slide_utils import load_wasabi_tree, get_slide_pairs

DATE_STR = date.today().isoformat()

def main():
    parser = argparse.ArgumentParser(description="Perform slide registration with VALIS")
    parser.add_argument("--cd8_slide", help="Path to CD8 slide")
    parser.add_argument("--he_slide", help="Path to H&E slide")
    parser.add_argument("--wasabi_json", help="Path to wasabi_file_tree.json for automatic selection")
    parser.add_argument("--pair_index", type=int, help="Index of slide pair to use (1-based)")
    parser.add_argument("--output_dir", required=True, help="Path to output directory")
    args = parser.parse_args()

    output_dir = args.output_dir

    # Determine slide paths either from arguments or the wasabi JSON file
    if args.wasabi_json and args.pair_index is not None:
        tree = load_wasabi_tree(args.wasabi_json)
        pairs = get_slide_pairs(tree)
        if args.pair_index < 1 or args.pair_index > len(pairs):
            print(f"Error: pair_index {args.pair_index} out of range. Found {len(pairs)} pairs.")
            sys.exit(1)
        selected = pairs[args.pair_index - 1]
        cd8_slide = selected["cd8_slide"]
        he_slide = selected["he_slide"]
        print(f"Selected pair {selected['pair_name']}\n  CD8: {cd8_slide}\n  HE: {he_slide}")
    elif args.cd8_slide and args.he_slide:
        cd8_slide = args.cd8_slide
        he_slide = args.he_slide
    else:
        parser.error("Provide --cd8_slide and --he_slide or --wasabi_json with --pair_index")

    # Prepare subdirectories for results and evaluation
    results_dir = os.path.join(output_dir, "registration_results")
    eval_dir = os.path.join(output_dir, "registration_evaluation")

    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(eval_dir, exist_ok=True)

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
    # Initialize VALIS with the CD8 slide explicitly set as the reference image.
    # Using the slide directory for ``src_dir`` helps VALIS locate the images
    # when absolute paths are provided.
    registrar = registration.Valis(
        src_dir=os.path.dirname(cd8_slide),  # Directory containing the slides
        dst_dir=output_dir,                  # Destination directory
        img_list=slide_paths
    )

    # Perform registration
    registrar.register()

    # Warp and save the registered slides to the output directory
    print(f"Warping and saving aligned slides to: {results_dir}")
    registrar.warp_and_save_slides(results_dir, crop="overlap")
    
    # Clean up the JVM as recommended
    print("Cleaning up resources...")
    registration.kill_jvm()
    
    elapsed_time = time.time() - start_time
    print(f"Registration completed in {elapsed_time:.2f} seconds")
    print(f"Results saved to: {results_dir}")
    
    # Return success status for shell script
    return 0

if __name__ == "__main__":
    sys.exit(main())
