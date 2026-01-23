# U-2-Net Image Segmentation

This application uses U-2-Net for salient object detection and segmentation. It processes all images in the input folder and outputs segmented objects on white backgrounds.

## Features

- Automatic batch processing of all images in a folder
- U-2-Net based segmentation using rembg library
- White background conversion
- Visual display of before/after results
- Supports multiple image formats (JPG, PNG, BMP, TIFF, WEBP)

## Installation

### Using Virtual Environment (Recommended)

A virtual environment isolates the project dependencies from your system Python, keeping your system clean.

**Option 1: Using the setup scripts (Windows)**

1. Double-click `setup_venv.bat` to create the virtual environment
2. Double-click `activate_venv.bat` to activate it and open a command prompt
3. Install dependencies:
```bash
pip install -r requirements.txt
```

**Option 2: Manual setup (Windows/Linux/Mac)**

1. Create virtual environment:
```bash
python -m venv venv
```

2. Activate virtual environment:
   - **Windows:**
     ```bash
     venv\Scripts\activate
     ```
   - **Linux/Mac:**
     ```bash
     source venv/bin/activate
     ```

3. Install required dependencies:
```bash
pip install -r requirements.txt
```

**Note:** 
- The virtual environment will be created in a `venv/` folder in your project directory
- On first run, the rembg library will automatically download the U-2-Net model weights (~176MB). This is a one-time download.
- To deactivate the virtual environment later, simply type: `deactivate`

## Usage

**Important:** Make sure your virtual environment is activated before running the application!

**Quick Start (Windows):**
1. Double-click `setup_venv.bat` (first time only)
2. Double-click `run.bat` to run the application

**Manual Steps:**

1. Activate virtual environment (if not already activated):
   - **Windows:** Double-click `activate_venv.bat` or run `venv\Scripts\activate`
   - **Linux/Mac:** Run `source venv/bin/activate`

2. Place your images in the `input/` folder

3. Run the application:
```bash
python app.py
```

4. Processed images will be saved in the `output/` folder with white backgrounds

## Folder Structure

```
PROJECT/
├── app.py              # Main application script
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── setup_venv.bat     # Script to create virtual environment (Windows)
├── activate_venv.bat  # Script to activate virtual environment (Windows)
├── run.bat            # Script to run the application (Windows)
├── venv/              # Virtual environment (created after setup)
├── input/             # Place your images here
└── output/            # Processed images will be saved here
```

## Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- TIFF (.tiff, .tif)
- WEBP (.webp)

## How It Works

1. The application scans the `input/` folder for images
2. Each image is processed using U-2-Net to detect and segment the main object
3. The background is replaced with white (#FFFFFF)
4. Results are saved to the `output/` folder
5. Before/after comparison is displayed (if matplotlib is available)

## Requirements

- Python 3.7+
- PyTorch (automatically installed via requirements.txt)
- CUDA-capable GPU (optional, but recommended for faster processing)

## Troubleshooting

- **Model download issues**: Ensure you have internet connection on first run
- **Memory errors**: Process images one at a time or resize large images
- **Display not working**: Install matplotlib: `pip install matplotlib`
