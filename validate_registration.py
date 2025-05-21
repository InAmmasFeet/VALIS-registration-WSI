#!/usr/bin/env python
# Registration validation script for VALIS registered slides

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import tifffile
from skimage.metrics import structural_similarity as ssim
from skimage.metrics import mean_squared_error
from skimage import exposure
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

def load_slide(filepath):
    """Load an OME-TIFF slide and return as numpy array"""
    try:
        print(f"Loading slide: {filepath}")
        slide = tifffile.imread(filepath)
        print(f"  Shape: {slide.shape}")
        return slide
    except Exception as e:
        print(f"Error loading slide {filepath}: {e}")
        return None

def extract_tile(slide, x, y, size=512):
    """Extract a tile from the slide at position (x,y) with given size"""
    try:
        # Check if coordinates are valid
        if x < 0 or y < 0 or x + size > slide.shape[1] or y + size > slide.shape[0]:
            print(f"Invalid coordinates: ({x}, {y}) with size {size} for slide shape {slide.shape}")
            return None

        # Extract the tile
        tile = slide[y:y+size, x:x+size]
        return tile
    except Exception as e:
        print(f"Error extracting tile at ({x}, {y}): {e}")
        return None

def calculate_metrics(tile1, tile2):
    """Calculate registration quality metrics between two tiles"""
    results = {}

    # Convert to grayscale if multi-channel
    if len(tile1.shape) > 2 and tile1.shape[2] > 1:
        gray1 = np.mean(tile1, axis=2).astype(np.uint8)
    else:
        gray1 = tile1.astype(np.uint8)

    if len(tile2.shape) > 2 and tile2.shape[2] > 1:
        gray2 = np.mean(tile2, axis=2).astype(np.uint8)
    else:
        gray2 = tile2.astype(np.uint8)

    # Normalize for better comparison
    gray1 = exposure.rescale_intensity(gray1)
    gray2 = exposure.rescale_intensity(gray2)

    try:
        # Calculate SSIM (higher is better, max 1.0)
        ssim_value = ssim(gray1, gray2, data_range=gray2.max() - gray2.min())
        results['ssim'] = ssim_value

        # Calculate MSE (lower is better)
        mse_value = mean_squared_error(gray1, gray2)
        results['mse'] = mse_value

        # Calculate normalized cross-correlation (higher is better, max 1.0)
        norm1 = gray1 - np.mean(gray1)
        norm2 = gray2 - np.mean(gray2)
        correlation = np.sum(norm1 * norm2) / (np.sqrt(np.sum(norm1**2)) * np.sqrt(np.sum(norm2**2)))
        results['correlation'] = correlation

        return results
    except Exception as e:
        print(f"Error calculating metrics: {e}")
        return {'ssim': 0, 'mse': float('inf'), 'correlation': 0}

def visualize_tiles(tile1, tile2, he_name, cd8_name, coords, metrics, output_path=None):
    """Visualize the side-by-side comparison of tiles with metrics"""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # Display H&E tile
    axes[0].imshow(tile1)
    axes[0].set_title(f"{he_name}\n({coords[0]}, {coords[1]})")
    axes[0].axis('off')

    # Display CD8 tile
    axes[1].imshow(tile2)
    axes[1].set_title(f"{cd8_name}\n({coords[0]}, {coords[1]})")
    axes[1].axis('off')

    # Create overlay to show registration accuracy
    if len(tile1.shape) == 3 and tile1.shape[2] == 3 and len(tile2.shape) == 2:
        # If H&E is RGB and CD8 is grayscale, create a combined image
        overlay = tile1.copy()
        # Normalize CD8 to 0-1 range and use it as the red channel
        cd8_norm = exposure.rescale_intensity(tile2.astype(float), out_range=(0, 1))
        overlay[:,:,0] = (cd8_norm * 255).astype(np.uint8)  # Red channel
    else:
        # Simple additive blend
        if len(tile1.shape) == 3 and len(tile2.shape) == 2:
            # Convert grayscale to RGB
            tile2_rgb = np.stack([tile2] * 3, axis=2)
        elif len(tile1.shape) == 2 and len(tile2.shape) == 3:
            tile1_rgb = np.stack([tile1] * 3, axis=2)
            tile2_rgb = tile2
        elif len(tile1.shape) == 2 and len(tile2.shape) == 2:
            tile1_rgb = np.stack([tile1] * 3, axis=2)
            tile2_rgb = np.stack([tile2] * 3, axis=2)
        else:
            tile1_rgb = tile1
            tile2_rgb = tile2

        # Create a simple overlay
        overlay = (0.5 * tile1_rgb + 0.5 * tile2_rgb).astype(np.uint8)

    axes[2].imshow(overlay)
    axes[2].set_title(f"Overlay\nSSIM: {metrics['ssim']:.3f}, Corr: {metrics['correlation']:.3f}")
    axes[2].axis('off')

    plt.tight_layout()

    # Add metrics as text
    metrics_text = (
        f"Registration Metrics:\n"
        f"SSIM: {metrics['ssim']:.4f} (higher is better, max 1.0)\n"
        f"MSE: {metrics['mse']:.4f} (lower is better)\n"
        f"Correlation: {metrics['correlation']:.4f} (higher is better, max 1.0)"
    )
    plt.figtext(0.5, 0.01, metrics_text, ha='center', fontsize=10,
                bbox={"facecolor":"white", "alpha":0.8, "pad":5})

    # Save if output path is provided
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved visualization to {output_path}")

    plt.close()

def main():
    # Define paths
    registration_dir = "/Users/sashurameshbabu/WSI slides/registration_results/registered_slides"
    he_path = os.path.join(registration_dir, "HE_downsampled_x2.ome.tiff")
    cd8_path = os.path.join(registration_dir, "CD8_channel2.ome.tiff")

    # Create output directory for visualizations
    output_dir = os.path.join(os.path.dirname(registration_dir), "validation_results")
    os.makedirs(output_dir, exist_ok=True)

    # Load slides
    he_slide = load_slide(he_path)
    cd8_slide = load_slide(cd8_path)

    if he_slide is None or cd8_slide is None:
        print("Failed to load one or both slides. Exiting.")
        sys.exit(1)

    # Print slide information
    print("\nSlide Information:")
    print(f"H&E Slide: {he_slide.shape}")
    print(f"CD8 Slide: {cd8_slide.shape}")

    # Check if slides have the same dimensions
    if he_slide.shape[:2] != cd8_slide.shape[:2]:
        print("Warning: Slides have different dimensions. Registration may not be valid.")
        print(f"  H&E shape: {he_slide.shape[:2]}")
        print(f"  CD8 shape: {cd8_slide.shape[:2]}")

    # Define tile size
    tile_size = 512

    # Define sample coordinates to extract (can be adjusted based on slide size)
    # We'll extract from top-left, center, and bottom-right
    height, width = min(he_slide.shape[0], cd8_slide.shape[0]), min(he_slide.shape[1], cd8_slide.shape[1])

    coordinates = [
        (width // 4, height // 4),               # Top-left region
        (width // 2, height // 2),               # Center region
        (3 * width // 4, 3 * height // 4)        # Bottom-right region
    ]

    # Create PDF for combined output
    pdf_path = os.path.join(output_dir, "registration_validation.pdf")
    with PdfPages(pdf_path) as pdf:
        # Iterate through coordinates and extract tiles
        all_metrics = []
        for i, (x, y) in enumerate(coordinates):
            print(f"\nExtracting tile {i+1} at coordinates ({x}, {y})")

            # Extract tiles
            he_tile = extract_tile(he_slide, x, y, tile_size)
            cd8_tile = extract_tile(cd8_slide, x, y, tile_size)

            if he_tile is None or cd8_tile is None:
                print(f"Skipping tile {i+1} due to extraction error")
                continue

            # Calculate metrics
            metrics = calculate_metrics(he_tile, cd8_tile)
            all_metrics.append(metrics)

            print(f"Tile {i+1} metrics:")
            print(f"  SSIM: {metrics['ssim']:.4f} (higher is better, max 1.0)")
            print(f"  MSE: {metrics['mse']:.4f} (lower is better)")
            print(f"  Correlation: {metrics['correlation']:.4f} (higher is better, max 1.0)")

            # Visualize and save individual comparison
            img_path = os.path.join(output_dir, f"tile_{i+1}_comparison.png")
            visualize_tiles(he_tile, cd8_tile, "H&E", "CD8", (x, y), metrics, img_path)

            # Also add to PDF
            plt.figure(figsize=(15, 5))
            visualize_tiles(he_tile, cd8_tile, "H&E", "CD8", (x, y), metrics)
            pdf.savefig(bbox_inches='tight')
            plt.close()

        # Calculate and display overall metrics
        if all_metrics:
            avg_ssim = np.mean([m['ssim'] for m in all_metrics])
            avg_mse = np.mean([m['mse'] for m in all_metrics])
            avg_corr = np.mean([m['correlation'] for m in all_metrics])

            print("\nOverall Registration Metrics (average across all tiles):")
            print(f"  Average SSIM: {avg_ssim:.4f}")
            print(f"  Average MSE: {avg_mse:.4f}")
            print(f"  Average Correlation: {avg_corr:.4f}")

            # Add a summary page to the PDF
            plt.figure(figsize=(8, 6))
            plt.text(0.5, 0.5,
                    f"Registration Validation Summary\n\n"
                    f"Number of tiles analyzed: {len(all_metrics)}\n\n"
                    f"Average SSIM: {avg_ssim:.4f}\n"
                    f"Average MSE: {avg_mse:.4f}\n"
                    f"Average Correlation: {avg_corr:.4f}\n\n"
                    f"Individual tile metrics are shown on previous pages.",
                    horizontalalignment='center',
                    verticalalignment='center',
                    transform=plt.gca().transAxes,
                    bbox={"facecolor":"white", "alpha":0.8, "pad":5})
            plt.axis('off')
            pdf.savefig(bbox_inches='tight')
            plt.close()

    print(f"\nValidation complete. Results saved to {output_dir}")
    print(f"PDF report saved to {pdf_path}")

if __name__ == "__main__":
    main()

