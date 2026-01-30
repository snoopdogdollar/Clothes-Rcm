"""
U-2-Net Image Segmentation and Clothing Classification Application
Processes all images: Segmentation -> Classification
"""

import sys
import re
from pathlib import Path
from PIL import Image

# Import utilities
from utils.segmentation import segment_image
from utils.classification import classify_clothing

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

def sanitize_filename(text):
    """
    Sanitize text to be safe for use in filenames.
    
    Args:
        text: Text to sanitize
    
    Returns:
        str: Sanitized filename-safe text
    """
    # Replace spaces and special characters with underscores
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

def process_image(input_path, output_folder, model_path=None, class_names_path=None):
    """
    Process a single image: Segmentation -> Classification
    
    Args:
        input_path: Path to input image
        output_folder: Folder to save output image
        model_path: Path to .pth model file (optional, uses default if not provided)
        class_names_path: Path to class_names.json (optional)
    
    Returns:
        tuple: (success: bool, clothing_category: str, confidence: float, output_path: Path)
    """
    try:
        # Read input image
        print(f"Processing: {input_path.name}")
        input_image = Image.open(input_path)
        
        # Convert to RGB if necessary
        if input_image.mode != 'RGB':
            input_image = input_image.convert('RGB')
        
        # Step 1: Segment image
        result_image = segment_image(input_image)
        
        # Step 2: Classify clothing
        clothing_category = "Unknown"
        confidence = 0.0
        try:
            print("  Classifying clothing type...")
            clothing_category, confidence = classify_clothing(
                result_image, 
                model_path=model_path, 
                class_names_path=class_names_path
            )
            print(f"  Predicted: {clothing_category} (confidence: {confidence:.2%})")
        except Exception as e:
            print(f"  Classification failed: {str(e)}")
        
        # Step 3: Create output filename with classification
        # Format: "category - original_filename.png"
        sanitized_category = sanitize_filename(clothing_category)
        original_stem = input_path.stem
        output_filename = f"{sanitized_category} - {original_stem}.png"
        output_path = output_folder / output_filename
        
        # Save the segmented result
        result_image.save(output_path, 'PNG')
        print(f"Saved: {output_path.name}")
        
        return True, clothing_category, confidence, output_path
        
    except Exception as e:
        print(f"Error processing {input_path.name}: {str(e)}")
        return False, "Unknown", 0.0, None


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
    models_folder = project_root / 'models'
    
    # Create folders if they don't exist
    input_folder.mkdir(exist_ok=True)
    output_folder.mkdir(exist_ok=True)
    models_folder.mkdir(exist_ok=True)
    
    # Check for model files
    model_path = models_folder / 'clothing_classifier.pth'
    class_names_path = models_folder / 'class_names.json'
    
    if not model_path.exists():
        print("\n" + "="*60)
        print("WARNING: Model file not found!")
        print("="*60)
        print(f"Expected location: {model_path}")
        print("\nPlease:")
        print("1. Create a 'models' folder in your project directory")
        print("2. Place your .pth model file as 'clothing_classifier.pth'")
        print("3. Place your class_names.json file in the same folder")
        print("="*60 + "\n")
        print("Continuing without classification...\n")
        model_path = None
        class_names_path = None
    
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
    print(f"Output folder: {output_folder}")
    if model_path and model_path.exists():
        print(f"Model: {model_path}")
    print()
    
    # Process each image
    successful = 0
    failed = 0
    classifications = []
    
    for image_file in image_files:
        # Process image (segmentation + classification)
        result = process_image(image_file, output_folder, model_path, class_names_path)
        if isinstance(result, tuple) and len(result) == 4:
            success, category, confidence, output_path = result
        else:
            success = False
            category = "Unknown"
            confidence = 0.0
            output_path = None
        
        if success:
            successful += 1
            classifications.append((image_file.name, category, confidence, output_path.name if output_path else "N/A"))
            # Display results
            #display_results(image_file, output_path)
        else:
            failed += 1
    
    # Summary
    print(f"\n{'='*50}")
    print(f"Processing complete!")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    
    if classifications:
        print(f"\nClassification Results:")
        print(f"{'='*50}")
        for filename, category, conf, output_name in classifications:
            print(f"{filename} -> {output_name}")
            print(f"  Category: {category} ({conf:.2%})")
    
    print(f"{'='*50}")
    print(f"Output saved to: {output_folder}")
    print(f"{'='*50}\n")


if __name__ == '__main__':
    main()