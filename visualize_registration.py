#!/usr/bin/env python3
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from PIL import Image
import cv2
import glob
import random

# Activate the correct environment if needed
# Use conda environment as per user memory
import sys
print(f"Using Python: {sys.executable}")
print(f"Python version: {sys.version}")

# Set base directories - these should be adjusted based on the actual paths
BASE_DIR = os.path.expanduser("~/WSI slides")
if not os.path.exists(BASE_DIR):
    # Try without space in name
    BASE_DIR = os.path.expanduser("~/WSI_slides")
    if not os.path.exists(BASE_DIR):
        print("Could not find WSI slides directory. Please adjust the BASE_DIR in the script.")
        BASE_DIR = os.path.expanduser("~")
        print(f"Using home directory instead: {BASE_DIR}")

# Define paths (will try multiple potential locations)
potential_matrix_paths = [
    os.path.join(BASE_DIR, "registration_matrix.npz"),
    os.path.join(BASE_DIR, "registration_results", "registration_matrix.npz"),
    os.path.join(BASE_DIR, "registration_results", "data", "registration_matrix.npz")
]

potential_he_tile_paths = [
    os.path.join(BASE_DIR, "he_tiles"),
    os.path.join(BASE_DIR, "registration_results", "matched_tiles", "he_tiles"),
    os.path.join(BASE_DIR, "registration_results", "matched_tiles", "he"),
    os.path.join(BASE_DIR, "matched_tiles", "he_tiles"),
    os.path.join(BASE_DIR, "matched_tiles", "he")
]

potential_cd8_tile_paths = [
    os.path.join(BASE_DIR, "cd8_tiles"),
    os.path.join(BASE_DIR, "registration_results", "matched_tiles", "cd8_tiles"),
    os.path.join(BASE_DIR, "registration_results", "matched_tiles", "cd8"),
    os.path.join(BASE_DIR, "matched_tiles", "cd8_tiles"),
    os.path.join(BASE_DIR, "matched_tiles", "cd8")
]

# Output directory for visualizations
output_dir = os.path.join(BASE_DIR, "visualizations")
os.makedirs(output_dir, exist_ok=True)

# Find valid paths
matrix_path = None
for path in potential_matrix_paths:
    if os.path.exists(path):
        matrix_path = path
        break

he_tiles_dir = None
for path in potential_he_tile_paths:
    if os.path.exists(path):
        he_tiles_dir = path
        break

cd8_tiles_dir = None
for path in potential_cd8_tile_paths:
    if os.path.exists(path):
        cd8_tiles_dir = path
        break

print(f"Matrix path: {matrix_path}")
print(f"HE tiles directory: {he_tiles_dir}")
print(f"CD8 tiles directory: {cd8_tiles_dir}")

def load_registration_matrix():
    """Loads the registration matrix from the NPZ file."""
    if matrix_path is None:
        print("Registration matrix file not found.")
        return np.eye(3)  # Return identity matrix as fallback
    
    try:
        # Load the .npz file
        data = np.load(matrix_path)
        
        # Display all keys in the file
        print(f"Keys in the registration matrix file: {list(data.keys())}")
        
        # Try to find matrix with common names
        matrix_keys = ['matrix', 'registration_matrix', 'transform_matrix', 'homography']
        matrix = None
        
        for key in matrix_keys:
            if key in data:
                matrix = data[key]
                break
        
        # If no known key found, use the first array
        if matrix is None and len(data.keys()) > 0:
            first_key = list(data.keys())[0]
            matrix = data[first_key]
            print(f"Using key '{first_key}' for matrix")
        
        # If we still don't have a matrix, return identity
        if matrix is None:
            print("Could not find matrix in NPZ file. Using identity matrix.")
            return np.eye(3)
        
        print("Registration matrix:")
        print(matrix)
        return matrix
        
    except Exception as e:
        print(f"Error loading registration matrix: {e}")
        return np.eye(3)  # Return identity matrix on error

def find_matching_tile_pairs(he_dir, cd8_dir, limit=5):
    """Finds matching tile pairs from both directories."""
    if he_dir is None or cd8_dir is None:
        print("Tile directories not found.")
        return []
    
    try:
        # Get lists of all image files
        he_tiles = glob.glob(os.path.join(he_dir, "*.png")) + glob.glob(os.path.join(he_dir, "*.jpg"))
        cd8_tiles = glob.glob(os.path.join(cd8_dir, "*.png")) + glob.glob(os.path.join(cd8_dir, "*.jpg"))
        
        print(f"Found {len(he_tiles)} HE tiles and {len(cd8_tiles)} CD8 tiles")
        
        # Extract tile identifiers to match pairs
        matching_pairs = []
        he_ids = {}
        
        # Extract identifiers from filenames (assuming common naming pattern)
        for he_path in he_tiles:
            filename = os.path.basename(he_path)
            # Try different identifier formats
            identifier = os.path.splitext(filename)[0]  # Without extension
            he_ids[identifier] = he_path
        
        # Find matching CD8 tiles
        for cd8_path in cd8_tiles:
            filename = os.path.basename(cd8_path)
            identifier = os.path.splitext(filename)[0]
            
            if identifier in he_ids:
                matching_pairs.append((he_ids[identifier], cd8_path))
                if len(matching_pairs) >= limit:
                    break
        
        # If no matches found, try to match by index
        if not matching_pairs and he_tiles and cd8_tiles:
            print("No matching filenames found. Matching by index...")
            for i in range(min(limit, min(len(he_tiles), len(cd8_tiles)))):
                matching_pairs.append((he_tiles[i], cd8_tiles[i]))
        
        print(f"Found {len(matching_pairs)} matching tile pairs")
        return matching_pairs
        
    except Exception as e:
        print(f"Error finding matching tile pairs: {e}")
        return []

def create_side_by_side_comparison(he_path, cd8_path, output_path, index):
    """Creates a side-by-side comparison of matching HE and CD8 tiles."""
    try:
        # Read images
        he_img = cv2.imread(he_path)
        cd8_img = cv2.imread(cd8_path)
        
        if he_img is None or cd8_img is None:
            print(f"Error loading images for comparison {index}")
            return False
        
        # Convert to RGB for matplotlib
        he_img_rgb = cv2.cvtColor(he_img, cv2.COLOR_BGR2RGB)
        cd8_img_rgb = cv2.cvtColor(cd8_img, cv2.COLOR_BGR2RGB)
        
        # Create figure with side-by-side comparison
        fig = plt.figure(figsize=(12, 6))
        gs = GridSpec(1, 2, figure=fig)
        
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.imshow(he_img_rgb)
        ax1.set_title('H&E Tile')
        ax1.axis('off')
        
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.imshow(cd8_img_rgb)
        ax2.set_title('CD8 Tile')
        ax2.axis('off')
        
        plt.suptitle(f'Tile Pair Comparison {index}')
        plt.tight_layout()
        
        # Save figure
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        print(f"Saved comparison {index} to {output_path}")
        return True
        
    except Exception as e:
        print(f"Error creating side-by-side comparison {index}: {e}")
        return False

def main():
    """Main function to execute all visualization tasks."""
    # Load and display registration matrix
    matrix = load_registration_matrix()
    
    # Find matching tile pairs
    matching_pairs = find_matching_tile_pairs(he_tiles_dir, cd8_tiles_dir)
    
    # Create side-by-side comparisons
    successful_comparisons = 0
    for i, (he_path, cd8_path) in enumerate(matching_pairs):
        output_path = os.path.join(output_dir, f"tile_comparison_{i+1}.png")
        if create_side_by_side_comparison(he_path, cd8_path, output_path, i+1):
            successful_comparisons += 1
    
    # Print summary
    print("\nSummary:")
    print("=" * 50)
    print(f"Registration Matrix Shape: {matrix.shape}")
    print(f"Registration Matrix Type: {matrix.dtype}")
    print("Registration Matrix Values:")
    print(matrix)
    print(f"\nCreated {successful_comparisons} side-by-side comparisons")
    print(f"Output directory: {output_dir}")
    print("=" * 50)

if __name__ == "__main__":
    main()

