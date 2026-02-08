"""
Quick test script to verify color extraction works with segmented images
"""

from PIL import Image
import numpy as np
from utils.color_extraction import extract_colors_simple

def test_color_extraction():
    """Test color extraction on a sample output image"""
    
    # Try to find a processed image in output folder
    from pathlib import Path
    output_folder = Path("output")
    
    if not output_folder.exists():
        print("No output folder found. Please run app.py first to generate segmented images.")
        return
    
    # Get first PNG file
    png_files = list(output_folder.glob("*.png"))
    if not png_files:
        print("No PNG files found in output folder. Please run app.py first.")
        return
    
    test_image_path = png_files[0]
    print(f"Testing color extraction on: {test_image_path.name}")
    print("="*60)
    
    # Load image
    img = Image.open(test_image_path)
    print(f"Image mode: {img.mode}")
    print(f"Image size: {img.size}")
    
    # Extract colors
    try:
        color_info = extract_colors_simple(img, num_colors=3)
        
        print(f"\n✓ Color extraction successful!")
        print(f"\nPrimary Color: {color_info['primary_color']}")
        print(f"Palette Type: {color_info['palette_type']}")
        
        print(f"\nDetailed Colors:")
        for i, color in enumerate(color_info['colors'], 1):
            print(f"  {i}. {color['name']:20s} - {color['hex']} ({color['percentage']:.1f}%)")
            print(f"     RGB: {color['rgb']}")
        
        print("\n" + "="*60)
        print("✓ Integration test passed!")
        
    except Exception as e:
        print(f"\n✗ Color extraction failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_color_extraction()
