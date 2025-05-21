#!/usr/bin/env python3
"""
Visualize Tile Pairs from Registered WSIs
=========================================

This script extracts and displays paired tiles from the CD8 and H&E slides
for visual comparison, along with their similarity scores.
"""

import os
import sys
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tifffile import TiffFile
from skimage.metrics import structural_similarity as ssim
from skimage.transform import resize

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Visualize tile pairs from registered slides')
    parser.add_argument('--cd8_slide', required=True, help='Path to registered CD8 OME-TIFF slide')
    parser.add_argument('--he_slide', required=True, help='Path to registered H&E OME-TIFF slide')
    parser.add_argument('--metrics_csv', required=True, help='Path to the tile similarity metrics CSV')
    parser.add_argument('--output_dir', required=True, help='Directory to save visualizations')
    parser.add_argument('--tile_size', type=int, default=256, help='Size of tiles in pixels (default: 256)')
    parser.add_argument('--downsample_factor', type=int, default=16, help='Factor to downsample the slides (default: 16)')
    parser.add_argument('--num_samples', type=int, default=5, help='Number of tile pairs to sample (default: 5)')
    return parser.parse_args()

def load_and_downsample_slide(slide_path, downsample_factor):
    """Load a slide and downsample it to reduce memory requirements."""
    print(f"Loading and downsampling {os.path.basename(slide_path)} (factor: {downsample_factor})...")

    with TiffFile(slide_path) as tif:
        # Get the first page
        page = tif.pages[0]
        is_multi_channel = len(page.shape) > 2
        img = page.asarray()

        print(f"Image shape: {img.shape}")

        # Downsample using simple slicing for speed
        if downsample_factor > 1:
            img = img[::downsample_factor, ::downsample_factor]
            if len(img.shape) > 2:
                img = img[:, :, :]  # Keep all channels

        print(f"Downsampled shape: {img.shape}")

    return img, is_multi_channel

def extract_tile(image, row, col, tile_size):
    """Extract a tile from the image at the specified position."""
    # Handle edge cases
    h, w = image.shape[:2]
    row_start = min(row * tile_size, h - tile_size)
    col_start = min(col * tile_size, w - tile_size)

    if len(image.shape) > 2:
        return image[row_start:row_start+tile_size, col_start:col_start+tile_size, :]
    else:
        return image[row_start:row_start+tile_size, col_start:col_start+tile_size]

def normalized_cross_correlation(image1, image2):
    """Calculate normalized cross-correlation between two images."""
    if len(image1.shape) > 2:  # Convert RGB to grayscale
        image1_gray = np.dot(image1[...,:3], [0.2989, 0.5870, 0.1140])
    else:
        image1_gray = image1

    if len(image2.shape) > 2:  # Convert RGB to grayscale
        image2_gray = np.dot(image2[...,:3], [0.2989, 0.5870, 0.1140])
    else:
        image2_gray = image2

    # Normalize images
    image1_norm = (image1_gray - np.mean(image1_gray)) / (np.std(image1_gray) + 1e-8)
    image2_norm = (image2_gray - np.mean(image2_gray)) / (np.std(image2_gray) + 1e-8)

    return np.mean(image1_norm * image2_norm)

def calculate_similarity(cd8_tile, he_tile):
    """Calculate similarity metrics between two tiles."""
    # Convert to grayscale if needed
    if len(cd8_tile.shape) > 2:
        cd8_gray = np.dot(cd8_tile[...,:3], [0.2989, 0.5870, 0.1140])
    else:
        cd8_gray = cd8_tile

    if len(he_tile.shape) > 2:
        he_gray = np.dot(he_tile[...,:3], [0.2989, 0.5870, 0.1140])
    else:
        he_gray = he_tile

    # Normalize images
    cd8_norm = (cd8_gray - np.mean(cd8_gray)) / (np.std(cd8_gray) + 1e-8)
    he_norm = (he_gray - np.mean(he_gray)) / (np.std(he_gray) + 1e-8)

    # Calculate metrics
    try:
        ssim_score = ssim(cd8_norm, he_norm, data_range=np.max(cd8_norm) - np.min(cd8_norm))
    except:
        ssim_score = 0

    try:
        ncc_score = normalized_cross_correlation(cd8_norm, he_norm)
    except:
        ncc_score = 0

    # Try a simple Pearson correlation coefficient as well
    try:
        cd8_flat = cd8_norm.flatten()
        he_flat = he_norm.flatten()
        pearson = np.corrcoef(cd8_flat, he_flat)[0, 1]
    except:
        pearson = 0

    return {
        'ssim': ssim_score,
        'ncc': ncc_score,
        'pearson': pearson
    }

def visualize_tile_pairs(cd8_img, he_img, metrics_df, output_dir, tile_size, num_samples):
    """Visualize pairs of tiles from the CD8 and H&E slides."""
    # Sort by combined score
    metrics_df['abs_combined_score'] = np.abs(metrics_df['combined_score'])

    # Get tile indices at different quality levels
    samples = []
    if len(metrics_df) >= num_samples:
        # Get best, worst, and middle tiles
        best_idx = metrics_df.nlargest(max(1, num_samples // 3), 'combined_score').index.tolist()
        worst_idx = metrics_df.nsmallest(max(1, num_samples // 3), 'combined_score').index.tolist()
        middle_idx = metrics_df.iloc[len(metrics_df)//2:len(metrics_df)//2 + max(1, num_samples - len(best_idx) - len(worst_idx))].index.tolist()
        samples = best_idx + worst_idx + middle_idx
    else:
        samples = metrics_df.index.tolist()

    # Extract row and column for each sample
    sample_info = []
    for idx in samples:
        sample_info.append({
            'index': idx,
            'row': idx // (cd8_img.shape[1] // tile_size),
            'col': idx % (cd8_img.shape[1] // tile_size),
            'combined_score': metrics_df.loc[idx, 'combined_score'],
            'ssim': metrics_df.loc[idx, 'ssim'],
            'ncc': metrics_df.loc[idx, 'ncc']
        })

    # Visualize each sample
    for sample in sample_info:
        # Extract tiles
        cd8_tile = extract_tile(cd8_img, sample['row'], sample['col'], tile_size)
        he_tile = extract_tile(he_img, sample['row'], sample['col'], tile_size)

        # Calculate similarity metrics live
        live_metrics = calculate_similarity(cd8_tile, he_tile)

        # Create visualization
        fig, axs = plt.subplots(1, 3, figsize=(15, 6))

        # Display CD8 tile
        if len(cd8_tile.shape) > 2 and cd8_tile.shape[2] == 3:
            axs[0].imshow(cd8_tile)
        else:
            axs[0].imshow(cd8_tile, cmap='gray')
        axs[0].set_title(f"CD8 Tile (Row {sample['row']}, Col {sample['col']})")
        axs[0].axis('off')

        # Display H&E tile
        if len(he_tile.shape) > 2 and he_tile.shape[2] == 3:
            axs[1].imshow(he_tile)
        else:
            axs[1].imshow(he_tile, cmap='gray')
        axs[1].set_title(f"H&E Tile (Row {sample['row']}, Col {sample['col']})")
        axs[1].axis('off')

        # Display overlay or difference
        if len(cd8_tile.shape) > 2 or len(he_tile.shape) > 2:
            # For RGB images, just show them side by side
            axs[2].text(0.5, 0.5, "RGB overlay not shown", horizontalalignment='center', verticalalignment='center')
            axs[2].axis('off')
        else:
            # For grayscale, show difference
            diff = np.abs(cd8_tile - he_tile)
            im = axs[2].imshow(diff, cmap='hot')
            axs[2].set_title("Absolute Difference")
            axs[2].axis('off')
            plt.colorbar(im, ax=axs[2], fraction=0.046, pad=0.04)

        # Add metrics as text
        metrics_text = (
            f"Similarity Metrics:\n"
            f"SSIM: {sample['ssim']:.4f} (CSV) / {live_metrics['ssim']:.4f} (Live)\n"
            f"NCC: {sample['ncc']:.4f} (CSV) / {live_metrics['ncc']:.4f} (Live)\n"
            f"Pearson: {live_metrics['pearson']:.4f} (Live)\n"
            f"Combined: {sample['combined_score']:.4f} (CSV)"
        )
        fig.text(0.5, 0.01, metrics_text, ha='center', fontsize=12, bbox=dict(facecolor='white', alpha=0.8))

        # Save figure
        output_path = os.path.join(output_dir, f"tile_comparison_idx{sample['index']}_row{sample['row']}_col{sample['col']}.png")
        plt.tight_layout()
        plt.savefig(output_path, dpi=200)
        plt.close()
        print(f"Saved comparison: {output_path}")

def main():
    """Main function."""
    args = parse_arguments()

    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    try:
        # Load metrics CSV
        metrics_df = pd.read_csv(args.metrics_csv)
        print(f"Loaded {len(metrics_df)} tile metrics from {args.metrics_csv}")

        # Load and downsample slides
        cd8_img, cd8_multi = load_and_downsample_slide(args.cd8_slide, args.downsample_factor)
        he_img, he_multi = load_and_downsample_slide(args.he_slide, args.downsample_factor)

        # Ensure images have the same dimensions for tile-based comparison
        min_h = min(cd8_img.shape[0], he_img.shape[0])
        min_w = min(cd8_img.shape[1], he_img.shape[1])
        cd8_img = cd8_img[:min_h, :min_w]
        he_img = he_img[:min_h, :min_w]
        print(f"Using common dimensions: {cd8_img.shape[:2]}")

        # Visualize tile pairs
        visualize_tile_pairs(cd8_img, he_img, metrics_df, args.output_dir, args.tile_size, args.num_samples)

        print(f"\nTile pair visualizations completed successfully.")
        print(f"Check the output directory: {args.output_dir}")

    except Exception as e:
        print(f"Error during visualization: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())

