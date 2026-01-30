"""
Segmentation utilities using U-2-Net for image segmentation.
"""
import warnings
from PIL import Image
import numpy as np
from skimage import morphology

# Suppress performance warnings from alpha matting
warnings.filterwarnings('ignore', category=UserWarning, message='.*PERFORMANCE WARNING.*')
warnings.filterwarnings('ignore', message='.*Thresholded incomplete Cholesky decomposition.*')

# Check if onnxruntime is installed
try:
    import onnxruntime
except ImportError:
    raise ImportError(
        "onnxruntime is not installed! Please install it: pip install onnxruntime"
    )

# Import rembg
try:
    from rembg import remove
except ImportError as e:
    raise ImportError(f"Failed to import rembg: {e}")


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
    dilated = morphology.dilation(binary_mask_bool, morphology.disk(band_width))
    eroded = morphology.erosion(binary_mask_bool, morphology.disk(band_width))
    
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


def segment_image(input_image):
    """
    Segment an image using U-2-Net with conditional alpha matting.
    
    Pipeline:
    1. Fast Segmentation (no alpha matting)
    2. Binary Mask
    3. Edge Band Extraction
    4. Edge Quality Check
    5. IF bad → Alpha Matting (edge only)
    6. ELSE → Direct Output
    
    Args:
        input_image: PIL Image (RGB)
    
    Returns:
        PIL Image: Segmented image with white background
    """
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
    
    # Step 6: Composite with white background
    white_background = np.ones_like(rgb) * 255
    
    # Apply alpha blending
    alpha_f = alpha.astype(np.float32) / 255.0
    result = (alpha_f[:, :, None] * rgb +
        (1 - alpha_f[:, :, None]) * white_background)
    
    # Convert back to PIL Image
    result_image = Image.fromarray(result.astype(np.uint8))
    
    return result_image