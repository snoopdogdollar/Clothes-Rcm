"""
U-2-Net Image Segmentation Application
Processes all images in the input folder and outputs segmented objects on white backgrounds.
"""

import sys
from pathlib import Path
from PIL import Image
import numpy as np
from skimage import morphology, measure
# Check if onnxruntime is installed
try:
    import onnxruntime
except ImportError:
    print("\n" + "="*60)
    print("ERROR: onnxruntime is not installed!")
    print("="*60)
    print(f"Python executable: {sys.executable}")
    print("\nTo fix this, please:")
    print("1. Activate your virtual environment:")
    print("   venv\\Scripts\\activate")
    print("2. Install requirements:")
    print("   pip install -r requirements.txt")
    print("   Or run: install_requirements.bat")
    print("="*60 + "\n")
    sys.exit(1)

# Import rembg
try:
    from rembg import remove
except ImportError as e:
    print("\n" + "="*60)
    print("ERROR: Failed to import rembg!")
    print("="*60)
    print(f"Error: {e}")
    print(f"Python executable: {sys.executable}")
    print("\nPossible solutions:")
    print("1. Make sure rembg is installed:")
    print("   pip install rembg")
    print("2. Or install all requirements:")
    print("   pip install -r requirements.txt")
    print("   Or run: install_requirements.bat")
    print("="*60 + "\n")
    raise

def extract_edge_band(binary_mask, band_width=3):
    """
    Extract edge pixels from binary mask.
    
    Args:
        binary_mask: Binary mask (0 or 255)
        band_width: Width of edge band in pixels
    
    Returns:
        Edge band mask
    """
    # Convert to boolean for morphological operations
    binary_mask_bool = binary_mask > 127
    
    # Create dilated and eroded masks
    dilated = morphology.binary_dilation(binary_mask_bool, morphology.disk(band_width))
    eroded = morphology.binary_erosion(binary_mask_bool, morphology.disk(band_width))
    
    # Edge band is pixels in dilated but not in eroded
    edge_band = dilated & ~eroded
    
    return edge_band.astype(np.uint8) * 255


def check_edge_quality(alpha, edge_band_mask):
    """
    Check edge quality using cheap metrics.
    
    Args:
        alpha: Alpha channel (0-255)
        edge_band_mask: Binary mask of edge band
    
    Returns:
        bool: True if edge quality is good, False if needs alpha matting
    """
    # Extract alpha values in edge band
    edge_alpha = alpha[edge_band_mask > 0]
    
    if len(edge_alpha) == 0:
        return True  # No edge, quality is fine
    
    # Calculate metrics
    # 1. Percentage of semi-transparent pixels (not fully opaque or transparent)
    semi_transparent = np.sum((edge_alpha > 10) & (edge_alpha < 245))
    semi_transparent_ratio = semi_transparent / len(edge_alpha) if len(edge_alpha) > 0 else 0
    
    # 2. Standard deviation of alpha values (higher = more variation = potentially jagged)
    alpha_std = np.std(edge_alpha) if len(edge_alpha) > 0 else 0
    
    # 3. Percentage of pixels near threshold boundaries (potential artifacts)
    near_boundary = np.sum((edge_alpha < 20) | (edge_alpha > 235))
    near_boundary_ratio = near_boundary / len(edge_alpha) if len(edge_alpha) > 0 else 0
    
    # Quality thresholds (tunable)
    # If too many semi-transparent pixels or high variation, quality is bad
    quality_good = (
        semi_transparent_ratio < 0.3 and  # Less than 30% semi-transparent
        alpha_std < 80 and  # Low variation
        near_boundary_ratio < 0.4  # Less than 40% near boundaries
    )
    
    return quality_good
def process_image(input_path, output_path):
    """
    Process a single image using U-2-Net segmentation with conditional alpha matting.
    
    Pipeline:
    1. Fast Segmentation (no alpha matting)
    2. Binary Mask
    3. Edge Band Extraction
    4. Edge Quality Check
    5. IF bad → Alpha Matting (edge only)
    6. ELSE → Direct Output
    
    Args:
        input_path: Path to input image
        output_path: Path to save output image
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Read input image
        print(f"Processing: {input_path.name}")
        input_image = Image.open(input_path)
        
        # Convert to RGB if necessary
        if input_image.mode != 'RGB':
            input_image = input_image.convert('RGB')
        
        # Step 1: Fast Segmentation (no alpha matting)
        output_image = remove(input_image, alpha_matting=False)
        
        # Convert to numpy array for processing
        output_array = np.array(output_image)
        
        # Extract alpha channel if present
        if output_array.shape[2] == 4:
            alpha = output_array[:, :, 3]
            rgb = output_array[:, :, :3]
        else:
            # If no alpha channel, use the image as is
            alpha = np.ones((output_array.shape[0], output_array.shape[1]), dtype=np.uint8) * 255
            rgb = output_array
        
        # Step 2: Create Binary Mask
        binary_mask = (alpha > 127).astype(np.uint8) * 255
        
        # Step 3: Extract Edge Band
        edge_band_mask = extract_edge_band(binary_mask, band_width=3)
        
        # Step 4: Check Edge Quality
        needs_alpha_matting = not check_edge_quality(alpha, edge_band_mask)
        
        # Step 5: Conditional Alpha Matting
        if needs_alpha_matting:
            print("  Edge quality poor, applying alpha matting...")
            # Re-run with alpha matting
            output_image_refined = remove(
                input_image,
                alpha_matting=True,
                alpha_matting_foreground_threshold=250,
                alpha_matting_background_threshold=10,
                alpha_matting_erode_size=15
            )
            output_array_refined = np.array(output_image_refined)
            if output_array_refined.shape[2] == 4:
                alpha = output_array_refined[:, :, 3]
                rgb = output_array_refined[:, :, :3]
        else:
            print("  Edge quality good, using direct output")
        
        # Step 6: Composite with white background
        white_background = np.ones_like(rgb) * 255
        
        # Apply alpha blending
        alpha_f = alpha.astype(np.float32) / 255.0
        result = (alpha_f[:, :, None] * rgb +
            (1 - alpha_f[:, :, None]) * white_background)
        
        # Convert back to PIL Image
        result_image = Image.fromarray(result.astype(np.uint8))
        
        # Save the result
        result_image.save(output_path, 'PNG')
        print(f"Saved: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"Error processing {input_path.name}: {str(e)}")
        return False


def display_results(input_path, output_path):
    """
    Display before and after images side by side.
    
    Args:
        input_path: Path to original image
        output_path: Path to processed image
    """
    try:
        import matplotlib.pyplot as plt
        
        # Load images
        original = Image.open(input_path)
        processed = Image.open(output_path)
        
        # Create figure with two subplots
        fig, axes = plt.subplots(1, 2, figsize=(15, 7))
        
        axes[0].imshow(original)
        axes[0].set_title('Original Image', fontsize=12)
        axes[0].axis('off')
        
        axes[1].imshow(processed)
        axes[1].set_title('Segmented Object (White Background)', fontsize=12)
        axes[1].axis('off')
        
        plt.tight_layout()
        plt.show()
        
    except ImportError:
        print("matplotlib not available. Skipping display.")
    except Exception as e:
        print(f"Error displaying results: {str(e)}")


def main():
    """Main function to process all images in the input folder."""
    
    # Define paths
    project_root = Path(__file__).parent
    input_folder = project_root / 'input'
    output_folder = project_root / 'output'
    
    # Create folders if they don't exist
    input_folder.mkdir(exist_ok=True)
    output_folder.mkdir(exist_ok=True)
    
    # Check if input folder exists and has images
    if not input_folder.exists():
        print(f"Error: Input folder '{input_folder}' does not exist.")
        print(f"Please create the folder and add images to process.")
        return
    
    # Get all image files
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}
    image_files = [f for f in input_folder.iterdir() 
                   if f.suffix.lower() in image_extensions]
    
    if not image_files:
        print(f"No images found in '{input_folder}' folder.")
        print(f"Supported formats: {', '.join(image_extensions)}")
        return
    
    print(f"\nFound {len(image_files)} image(s) to process.")
    print(f"Input folder: {input_folder}")
    print(f"Output folder: {output_folder}\n")
    
    # Process each image
    successful = 0
    failed = 0
    
    for image_file in image_files:
        # Create output filename (same name, PNG format)
        output_filename = image_file.stem + '.png'
        output_path = output_folder / output_filename
        
        # Process image
        if process_image(image_file, output_path):
            successful += 1
            # Display results
            #display_results(image_file, output_path)
        else:
            failed += 1
    
    # Summary
    print(f"\n{'='*50}")
    print(f"Processing complete!")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Output saved to: {output_folder}")
    print(f"{'='*50}\n")


if __name__ == '__main__':
    main()
