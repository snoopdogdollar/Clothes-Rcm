import numpy as np
import pandas as pd
import cv2
from PIL import Image
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from collections import Counter
import colorsys
import os
from tqdm import tqdm

# ============================
# 1. DETAILED COLOR DATABASE
# ============================

DETAILED_COLOR_DATABASE = {
    # REDS
    "Crimson": {"rgb": (220, 20, 60), "family": "Red"},
    "Burgundy": {"rgb": (128, 0, 32), "family": "Red"},
    "Maroon": {"rgb": (128, 0, 0), "family": "Red"},
    "Scarlet": {"rgb": (255, 36, 0), "family": "Red"},
    "Ruby": {"rgb": (224, 17, 95), "family": "Red"},
    "Cherry": {"rgb": (222, 49, 99), "family": "Red"},
    "Wine": {"rgb": (114, 47, 55), "family": "Red"},
    "Carmine": {"rgb": (150, 0, 24), "family": "Red"},
    "Coral": {"rgb": (255, 127, 80), "family": "Red-Orange"},
    "Salmon": {"rgb": (250, 128, 114), "family": "Red-Orange"},
    "Brick Red": {"rgb": (203, 65, 84), "family": "Red"},
    "Rose": {"rgb": (255, 0, 127), "family": "Red-Pink"},
    
    # PINKS
    "Blush": {"rgb": (222, 93, 131), "family": "Pink"},
    "Hot Pink": {"rgb": (255, 105, 180), "family": "Pink"},
    "Fuchsia": {"rgb": (255, 0, 255), "family": "Pink-Purple"},
    "Magenta": {"rgb": (255, 0, 255), "family": "Pink-Purple"},
    "Pink": {"rgb": (255, 192, 203), "family": "Pink"},
    "Baby Pink": {"rgb": (244, 194, 194), "family": "Pink"},
    "Rose Gold": {"rgb": (183, 110, 121), "family": "Pink-Brown"},
    
    # ORANGES
    "Orange": {"rgb": (255, 165, 0), "family": "Orange"},
    "Tangerine": {"rgb": (242, 133, 0), "family": "Orange"},
    "Peach": {"rgb": (255, 229, 180), "family": "Orange"},
    "Apricot": {"rgb": (251, 206, 177), "family": "Orange"},
    "Rust": {"rgb": (183, 65, 14), "family": "Orange-Brown"},
    "Terracotta": {"rgb": (226, 114, 91), "family": "Orange-Brown"},
    "Amber": {"rgb": (255, 191, 0), "family": "Yellow-Orange"},
    "Copper": {"rgb": (184, 115, 51), "family": "Orange-Brown"},
    
    # YELLOWS
    "Gold": {"rgb": (255, 215, 0), "family": "Yellow"},
    "Lemon": {"rgb": (255, 250, 205), "family": "Yellow"},
    "Mustard": {"rgb": (255, 219, 88), "family": "Yellow"},
    "Saffron": {"rgb": (244, 196, 48), "family": "Yellow-Orange"},
    "Canary": {"rgb": (255, 255, 153), "family": "Yellow"},
    "Sunflower": {"rgb": (255, 218, 3), "family": "Yellow"},
    
    # GREENS
    "Emerald": {"rgb": (80, 200, 120), "family": "Green"},
    "Jade": {"rgb": (0, 168, 107), "family": "Green"},
    "Olive": {"rgb": (128, 128, 0), "family": "Green"},
    "Forest Green": {"rgb": (34, 139, 34), "family": "Green"},
    "Lime": {"rgb": (0, 255, 0), "family": "Green"},
    "Mint": {"rgb": (152, 255, 152), "family": "Green"},
    "Sage": {"rgb": (188, 184, 138), "family": "Green-Gray"},
    "Chartreuse": {"rgb": (127, 255, 0), "family": "Green-Yellow"},
    "Kelly Green": {"rgb": (76, 187, 23), "family": "Green"},
    "Sea Green": {"rgb": (46, 139, 87), "family": "Green"},
    "Army Green": {"rgb": (75, 83, 32), "family": "Green"},
    
    # BLUES
    "Navy": {"rgb": (0, 0, 128), "family": "Blue"},
    "Royal Blue": {"rgb": (65, 105, 225), "family": "Blue"},
    "Cobalt": {"rgb": (0, 71, 171), "family": "Blue"},
    "Sapphire": {"rgb": (8, 37, 103), "family": "Blue"},
    "Azure": {"rgb": (0, 127, 255), "family": "Blue"},
    "Teal": {"rgb": (0, 128, 128), "family": "Blue-Green"},
    "Turquoise": {"rgb": (64, 224, 208), "family": "Blue-Green"},
    "Aqua": {"rgb": (0, 255, 255), "family": "Blue-Green"},
    "Sky Blue": {"rgb": (135, 206, 235), "family": "Blue"},
    "Steel Blue": {"rgb": (70, 130, 180), "family": "Blue"},
    "Baby Blue": {"rgb": (137, 207, 240), "family": "Blue"},
    "Powder Blue": {"rgb": (176, 224, 230), "family": "Blue"},
    "Denim Blue": {"rgb": (21, 96, 189), "family": "Blue"},
    "Chambray": {"rgb": (64, 123, 159), "family": "Blue"},
    "Electric Blue": {"rgb": (125, 249, 255), "family": "Blue"},
    
    # PURPLES
    "Lavender": {"rgb": (230, 230, 250), "family": "Purple"},
    "Violet": {"rgb": (238, 130, 238), "family": "Purple"},
    "Plum": {"rgb": (221, 160, 221), "family": "Purple"},
    "Orchid": {"rgb": (218, 112, 214), "family": "Purple"},
    "Mauve": {"rgb": (224, 176, 255), "family": "Purple"},
    "Lilac": {"rgb": (200, 162, 200), "family": "Purple"},
    "Eggplant": {"rgb": (97, 64, 81), "family": "Purple"},
    "Amethyst": {"rgb": (153, 102, 204), "family": "Purple"},
    "Grape": {"rgb": (111, 45, 168), "family": "Purple"},
    
    # BROWNS
    "Beige": {"rgb": (245, 245, 220), "family": "Brown"},
    "Taupe": {"rgb": (72, 60, 50), "family": "Brown-Gray"},
    "Khaki": {"rgb": (195, 176, 145), "family": "Brown"},
    "Camel": {"rgb": (193, 154, 107), "family": "Brown"},
    "Tan": {"rgb": (210, 180, 140), "family": "Brown"},
    "Coffee": {"rgb": (111, 78, 55), "family": "Brown"},
    "Chocolate": {"rgb": (123, 63, 0), "family": "Brown"},
    "Cinnamon": {"rgb": (210, 105, 30), "family": "Brown"},
    "Umber": {"rgb": (99, 81, 71), "family": "Brown"},
    "Sepia": {"rgb": (112, 66, 20), "family": "Brown"},
    "Oatmeal": {"rgb": (218, 207, 182), "family": "Brown"},
    "Caramel": {"rgb": (175, 111, 9), "family": "Brown"},
    
    # GRAYS
    "Charcoal": {"rgb": (54, 69, 79), "family": "Gray"},
    "Slate": {"rgb": (112, 128, 144), "family": "Gray"},
    "Ash": {"rgb": (178, 190, 181), "family": "Gray"},
    "Silver": {"rgb": (192, 192, 192), "family": "Gray"},
    "Stone": {"rgb": (160, 151, 137), "family": "Gray"},
    "Heather Gray": {"rgb": (152, 152, 152), "family": "Gray"},
    "Gunmetal": {"rgb": (42, 52, 57), "family": "Gray"},
    
    # WHITES
    "Pearl": {"rgb": (234, 224, 200), "family": "White"},
    "Ivory": {"rgb": (255, 255, 240), "family": "White"},
    "Cream": {"rgb": (255, 253, 208), "family": "White"},
    "Eggshell": {"rgb": (240, 234, 214), "family": "White"},
    "Off-White": {"rgb": (250, 249, 246), "family": "White"},
    "Snow": {"rgb": (255, 250, 250), "family": "White"},
    "White": {"rgb": (255, 255, 255), "family": "White"},
    
    # BLACKS
    "Jet Black": {"rgb": (0, 0, 0), "family": "Black"},
    "Onyx": {"rgb": (15, 15, 15), "family": "Black"},
    "Ebony": {"rgb": (24, 24, 24), "family": "Black"},
    "Black": {"rgb": (0, 0, 0), "family": "Black"},
}

# ============================
# 2. ADVANCED COLOR EXTRACTOR CLASS
# ============================

class KaggleColorExtractor:
    """
    Optimized color extractor for Kaggle notebook environment
    """
    
    def __init__(self, num_colors=5, method='kmeans_enhanced'):
        self.num_colors = num_colors
        self.method = method
        self.color_db = DETAILED_COLOR_DATABASE
    
    # ========== MAIN EXTRACTION FUNCTION ==========
    
    def extract_from_image(self, image_path_or_array, is_path=True):
        """
        Main function to extract colors from image
        
        Args:
            image_path_or_array: Path to image or numpy array
            is_path: True if first arg is path, False if numpy array
            
        Returns:
            Dictionary with detailed color analysis
        """
        # Load image
        if is_path:
            img = self._load_image(image_path_or_array)
        else:
            img = image_path_or_array
        
        if img is None:
            return self._get_default_colors()
        
        # Extract foreground pixels
        pixels = self._get_foreground_pixels(img)
        if len(pixels) == 0:
            return self._get_default_colors()
        
        # Apply clustering
        colors_rgb, percentages = self._cluster_colors(pixels)
        
        # Map to color names
        color_details = self._map_to_color_names(colors_rgb, percentages)
        
        # Create final result
        result = self._create_result(color_details, img.shape)
        
        return result
    
    # ========== IMAGE PROCESSING ==========
    
    def _load_image(self, image_path):
        """Load image with error handling"""
        try:
            # Try OpenCV first
            img = cv2.imread(image_path)
            if img is not None:
                return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Try PIL as fallback
            img = Image.open(image_path)
            return np.array(img.convert('RGB'))
            
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            return None
    
    def _get_foreground_pixels(self, img):
        """Extract foreground pixels (assumes background is removed)"""
        if len(img.shape) == 3 and img.shape[2] == 4:  # RGBA image
            alpha = img[:, :, 3]
            mask = alpha > 10  # Threshold for transparency
            pixels = img[mask][:, :3]  # Get RGB channels
        else:  # RGB image
            # Assume entire image is foreground
            pixels = img.reshape(-1, 3)
        
        return pixels
    
    # ========== COLOR CLUSTERING ==========
    
    def _cluster_colors(self, pixels):
        """Cluster pixels to find dominant colors"""
        if len(pixels) < 100:  # Not enough pixels
            # Use simple averaging
            avg_color = np.mean(pixels, axis=0).astype(int)
            return np.array([avg_color]), np.array([100.0])
        
        if self.method == 'simple_kmeans':
            return self._simple_kmeans(pixels)
        elif self.method == 'kmeans_enhanced':
            return self._enhanced_kmeans(pixels)
        elif self.method == 'adaptive_kmeans':
            return self._adaptive_kmeans(pixels)
        else:
            return self._enhanced_kmeans(pixels)  # Default
    
    def _simple_kmeans(self, pixels):
        """Simple K-Means clustering"""
        # Limit samples for speed
        if len(pixels) > 10000:
            indices = np.random.choice(len(pixels), 10000, replace=False)
            sample_pixels = pixels[indices]
        else:
            sample_pixels = pixels
        
        kmeans = KMeans(n_clusters=self.num_colors, n_init=5, random_state=42)
        kmeans.fit(sample_pixels)
        
        # Get cluster centers
        colors = kmeans.cluster_centers_.astype(int)
        
        # Predict labels for all pixels to get accurate percentages
        if len(pixels) > 10000:
            # Predict on sample for speed
            sample_labels = kmeans.predict(sample_pixels)
            unique, counts = np.unique(sample_labels, return_counts=True)
        else:
            labels = kmeans.predict(pixels)
            unique, counts = np.unique(labels, return_counts=True)
        
        percentages = (counts / len(sample_pixels) * 100).round(2)
        
        # Sort by percentage
        sorted_idx = np.argsort(percentages)[::-1]
        colors = colors[sorted_idx]
        percentages = percentages[sorted_idx]
        
        return colors, percentages
    
    def _enhanced_kmeans(self, pixels):
        """Enhanced K-Means with LAB color space"""
        # Convert to LAB color space (better for color perception)
        pixels_reshaped = pixels.reshape(-1, 1, 3).astype(np.uint8)
        pixels_lab = cv2.cvtColor(pixels_reshaped, cv2.COLOR_RGB2LAB)
        pixels_lab = pixels_lab.reshape(-1, 3)
        
        # Sample for speed
        if len(pixels_lab) > 5000:
            indices = np.random.choice(len(pixels_lab), 5000, replace=False)
            sample_lab = pixels_lab[indices]
        else:
            sample_lab = pixels_lab
        
        # Determine optimal k
        n_samples = len(sample_lab)
        optimal_k = min(self.num_colors, n_samples // 100)
        optimal_k = max(2, optimal_k)
        
        # Apply K-Means in LAB space
        kmeans = KMeans(n_clusters=optimal_k, n_init=5, random_state=42)
        kmeans.fit(sample_lab)
        
        # Get cluster centers in LAB
        lab_centers = kmeans.cluster_centers_
        
        # Convert LAB centers back to RGB
        rgb_centers = []
        for center in lab_centers:
            # Convert LAB to RGB
            center_rgb = cv2.cvtColor(
                np.uint8([[center]]), 
                cv2.COLOR_LAB2RGB
            )[0][0]
            rgb_centers.append(center_rgb)
        
        colors = np.array(rgb_centers).astype(int)
        
        # Calculate percentages
        sample_labels = kmeans.predict(sample_lab)
        unique, counts = np.unique(sample_labels, return_counts=True)
        percentages = (counts / len(sample_lab) * 100).round(2)
        
        # Sort by percentage
        sorted_idx = np.argsort(percentages)[::-1]
        colors = colors[sorted_idx]
        percentages = percentages[sorted_idx]
        
        return colors[:self.num_colors], percentages[:self.num_colors]
    
    def _adaptive_kmeans(self, pixels):
        """Adaptive K-Means that adjusts based on color complexity"""
        # Calculate color variance
        color_std = np.std(pixels, axis=0).mean()
        
        # Adjust number of clusters based on color complexity
        if color_std < 20:  # Low color variation
            n_clusters = min(3, self.num_colors)
        elif color_std < 50:  # Medium color variation
            n_clusters = min(5, self.num_colors)
        else:  # High color variation
            n_clusters = self.num_colors
        
        # Sample pixels
        if len(pixels) > 8000:
            indices = np.random.choice(len(pixels), 8000, replace=False)
            sample_pixels = pixels[indices]
        else:
            sample_pixels = pixels
        
        # Apply K-Means
        kmeans = KMeans(n_clusters=n_clusters, n_init=5, random_state=42)
        kmeans.fit(sample_pixels)
        
        colors = kmeans.cluster_centers_.astype(int)
        sample_labels = kmeans.predict(sample_pixels)
        
        unique, counts = np.unique(sample_labels, return_counts=True)
        percentages = (counts / len(sample_pixels) * 100).round(2)
        
        # Sort by percentage
        sorted_idx = np.argsort(percentages)[::-1]
        colors = colors[sorted_idx]
        percentages = percentages[sorted_idx]
        
        return colors, percentages
    
    # ========== COLOR MAPPING ==========
    
    def _map_to_color_names(self, colors_rgb, percentages):
        """Map RGB colors to detailed color names"""
        color_details = []
        
        for rgb, percentage in zip(colors_rgb, percentages):
            # Find closest color in database
            closest = self._find_closest_color(rgb)
            
            # Calculate additional color properties
            hsv = self._rgb_to_hsv(rgb)
            brightness = self._calculate_brightness(rgb)
            saturation = self._calculate_saturation(rgb)
            is_neutral = self._is_neutral_color(rgb)
            
            color_info = {
                'rgb': rgb.tolist(),
                'hex': self._rgb_to_hex(rgb),
                'name': closest['name'],
                'family': closest['family'],
                'percentage': float(percentage),
                'hsv': hsv,
                'brightness': float(brightness),
                'saturation': float(saturation),
                'is_neutral': is_neutral,
                'is_light': brightness > 0.7,
                'is_dark': brightness < 0.3,
                'is_vibrant': saturation > 0.7
            }
            
            color_details.append(color_info)
        
        return color_details
    
    def _find_closest_color(self, target_rgb):
        """Find the closest color name for given RGB"""
        min_distance = float('inf')
        closest_name = "Unknown"
        closest_family = "Unknown"
        
        target_np = np.array(target_rgb)
        
        for color_name, color_info in self.color_db.items():
            db_rgb = np.array(color_info['rgb'])
            distance = np.linalg.norm(target_np - db_rgb)
            
            if distance < min_distance:
                min_distance = distance
                closest_name = color_name
                closest_family = color_info['family']
        
        return {'name': closest_name, 'family': closest_family}
    
    # ========== COLOR UTILITIES ==========
    
    def _rgb_to_hex(self, rgb):
        """Convert RGB to HEX color code"""
        return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])
    
    def _rgb_to_hsv(self, rgb):
        """Convert RGB to HSV (hue: 0-360, saturation: 0-1, value: 0-1)"""
        r, g, b = rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        return [h*360, s, v]
    
    def _calculate_brightness(self, rgb):
        """Calculate brightness using luminance formula"""
        r, g, b = rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0
        return 0.299*r + 0.587*g + 0.114*b
    
    def _calculate_saturation(self, rgb):
        """Calculate color saturation"""
        r, g, b = rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0
        cmax = max(r, g, b)
        cmin = min(r, g, b)
        
        if cmax == 0:
            return 0.0
        return (cmax - cmin) / cmax
    
    def _is_neutral_color(self, rgb):
        """Check if color is neutral (black, white, gray, brown)"""
        r, g, b = rgb
        
        # Check for grayscale
        if abs(r - g) < 20 and abs(r - b) < 20:
            return True
        
        # Check for brown tones
        if 80 < r < 200 and 40 < g < 150 and 0 < b < 100:
            if r > g and g > b:  # Typical brown pattern
                return True
        
        # Check for beige/cream
        if r > 200 and g > 180 and b > 150:
            return True
        
        return False
    
    # ========== RESULT FORMATTING ==========
    
    def _create_result(self, color_details, image_shape):
        """Create final result dictionary"""
        # Find dominant color (highest percentage)
        dominant_color = max(color_details, key=lambda x: x['percentage'])
        
        # Analyze color palette
        palette_type = self._analyze_palette(color_details)
        
        # Calculate color statistics
        stats = self._calculate_statistics(color_details)
        
        # Generate color suggestions
        suggestions = self._generate_suggestions(color_details)
        
        return {
            'colors': color_details,
            'dominant_color': {
                'name': dominant_color['name'],
                'rgb': dominant_color['rgb'],
                'hex': dominant_color['hex'],
                'percentage': dominant_color['percentage']
            },
            'palette_type': palette_type,
            'statistics': stats,
            'suggestions': suggestions,
            'metadata': {
                'extraction_method': self.method,
                'num_colors_found': len(color_details),
                'image_size': f"{image_shape[1]}x{image_shape[0]}"
            }
        }
    
    def _analyze_palette(self, color_details):
        """Analyze the type of color palette"""
        families = [color['family'] for color in color_details]
        family_counts = Counter(families)
        
        # Check for different palette types
        if len(set(families)) == 1:
            return "Monochromatic"
        
        neutral_count = sum(1 for color in color_details if color['is_neutral'])
        if neutral_count >= len(color_details) // 2:
            return "Neutral Dominant"
        
        # Check for warm/cool balance
        warm_families = ['Red', 'Orange', 'Yellow', 'Red-Orange', 'Yellow-Orange']
        cool_families = ['Blue', 'Green', 'Purple', 'Blue-Green', 'Pink-Purple']
        
        warm_count = sum(1 for color in color_details if color['family'] in warm_families)
        cool_count = sum(1 for color in color_details if color['family'] in cool_families)
        
        if warm_count > 0 and cool_count > 0:
            return "Balanced Warm/Cool"
        elif warm_count > cool_count:
            return "Warm Palette"
        elif cool_count > warm_count:
            return "Cool Palette"
        
        return "Mixed Palette"
    
    def _calculate_statistics(self, color_details):
        """Calculate color statistics"""
        stats = {
            'total_colors': len(color_details),
            'neutral_colors': sum(1 for c in color_details if c['is_neutral']),
            'vibrant_colors': sum(1 for c in color_details if c['is_vibrant']),
            'light_colors': sum(1 for c in color_details if c['is_light']),
            'dark_colors': sum(1 for c in color_details if c['is_dark']),
            'avg_brightness': np.mean([c['brightness'] for c in color_details]),
            'avg_saturation': np.mean([c['saturation'] for c in color_details])
        }
        
        # Add color family distribution
        families = [c['family'] for c in color_details]
        family_dist = Counter(families)
        stats['family_distribution'] = dict(family_dist)
        
        return stats
    
    def _generate_suggestions(self, color_details):
        """Generate color pairing suggestions"""
        suggestions = []
        
        for color in color_details:
            if color['is_neutral']:
                suggestions.append({
                    'for_color': color['name'],
                    'advice': f"Neutral color - pairs well with any vibrant color",
                    'good_with': ['Red', 'Blue', 'Green', 'Purple'],
                    'avoid': ['Similar neutrals may create monotony']
                })
            elif color['is_vibrant']:
                suggestions.append({
                    'for_color': color['name'],
                    'advice': f"Vibrant color - best paired with neutrals",
                    'good_with': ['White', 'Black', 'Gray', 'Beige'],
                    'avoid': ['Other vibrant colors may clash']
                })
            else:
                suggestions.append({
                    'for_color': color['name'],
                    'advice': f"Muted color - versatile, pairs with many colors",
                    'good_with': ['Similar tones', 'Neutrals', 'Complementary colors'],
                    'avoid': ['Very similar muted colors']
                })
        
        return suggestions
    
    def _get_default_colors(self):
        """Return default colors when extraction fails"""
        return {
            'colors': [{
                'rgb': [128, 128, 128],
                'hex': '#808080',
                'name': 'Gray',
                'family': 'Gray',
                'percentage': 100.0,
                'hsv': [0, 0.0, 0.5],
                'brightness': 0.5,
                'saturation': 0.0,
                'is_neutral': True,
                'is_light': False,
                'is_dark': False,
                'is_vibrant': False
            }],
            'dominant_color': {
                'name': 'Gray',
                'rgb': [128, 128, 128],
                'hex': '#808080',
                'percentage': 100.0
            },
            'palette_type': 'Neutral',
            'statistics': {
                'total_colors': 1,
                'neutral_colors': 1,
                'vibrant_colors': 0
            },
            'suggestions': [],
            'metadata': {'error': 'No colors extracted'}
        }

# ============================
# 3. VISUALIZATION FUNCTIONS
# ============================

def display_image_with_colors(image_path, color_result, figsize=(16, 8)):
    """
    Display image with extracted color palette in one view
    
    Args:
        image_path: Path to the image file (or numpy array)
        color_result: Dictionary from extractor.extract_from_image()
        figsize: Figure size (width, height)
    """
    try:
        # Load image
        if isinstance(image_path, str):
            img = Image.open(image_path)
            img_array = np.array(img)
        else:
            # If it's already a numpy array
            img_array = image_path
            img = Image.fromarray(img_array.astype('uint8'))
        
        # Create figure
        fig = plt.figure(figsize=figsize)
        
        # Main grid: 2 rows, 3 columns
        gs = plt.GridSpec(2, 3, figure=fig, hspace=0.3, wspace=0.3)
        
        # 1. Image (Top row, full width)
        ax_img = fig.add_subplot(gs[0, :])
        ax_img.imshow(img_array)
        ax_img.set_title(' Original Image', fontsize=14, fontweight='bold', pad=10)
        ax_img.axis('off')
        
        # Add image info
        img_height, img_width = img_array.shape[:2]
        img_info = f"Size: {img_width}×{img_height}"
        if len(img_array.shape) == 3 and img_array.shape[2] == 4:
            img_info += " (RGBA)"
        elif len(img_array.shape) == 3:
            img_info += " (RGB)"
        
        ax_img.text(0.02, 0.98, img_info,
                   transform=ax_img.transAxes,
                   fontsize=10, color='white',
                   bbox=dict(boxstyle='round', facecolor='black', alpha=0.7),
                   verticalalignment='top')
        
        # 2. Color Palette (Bottom left)
        ax_palette = fig.add_subplot(gs[1, 0])
        ax_palette.set_title(' Color Palette', fontsize=12, fontweight='bold', pad=10)
        ax_palette.axis('off')
        
        colors = color_result['colors']
        n_colors = len(colors)
        
        # Create vertical color swatches
        for i, color in enumerate(colors):
            # Color swatch
            rect = plt.Rectangle((0, i), 1, 0.8, 
                               color=np.array(color['rgb'])/255.0,
                               edgecolor='black', linewidth=1)
            ax_palette.add_patch(rect)
            
            # Color name and percentage
            text_color = 'white' if color['brightness'] < 0.5 else 'black'
            ax_palette.text(0.5, i + 0.4, 
                           f"{color['name']}\n{color['percentage']:.1f}%",
                           ha='center', va='center',
                           color=text_color,
                           fontsize=9 if len(color['name']) < 15 else 8,
                           fontweight='bold')
        
        ax_palette.set_xlim(0, 1)
        ax_palette.set_ylim(0, n_colors)
        ax_palette.set_aspect('auto')
        
        # 3. Color Analysis (Bottom middle)
        ax_info = fig.add_subplot(gs[1, 1])
        ax_info.set_title(' Color Analysis', fontsize=12, fontweight='bold', pad=10)
        ax_info.axis('off')
        
        # Dominant color info
        dominant = color_result['dominant_color']
        info_text = f" Dominant Color:\n"
        info_text += f"• {dominant['name']}\n"
        info_text += f"• RGB: {dominant['rgb']}\n"
        info_text += f"• HEX: {dominant['hex']}\n"
        info_text += f"• Coverage: {dominant['percentage']:.1f}%\n\n"
        
        info_text += f" Palette Type:\n{color_result['palette_type']}\n\n"
        
        # Top 3 colors
        info_text += f" Top Colors:\n"
        for i, color in enumerate(color_result['colors'][:3], 1):
            info_text += f"{i}. {color['name']}: {color['percentage']:.1f}%\n"
        
        ax_info.text(0.05, 0.98, info_text,
                    transform=ax_info.transAxes,
                    fontsize=10, va='top',
                    linespacing=1.5)
        
        # 4. Statistics & Suggestions (Bottom right)
        ax_stats = fig.add_subplot(gs[1, 2])
        ax_stats.set_title(' Statistics & Tips', fontsize=12, fontweight='bold', pad=10)
        ax_stats.axis('off')
        
        # Statistics
        stats = color_result.get('statistics', {})
        stats_text = f" Statistics:\n"
        stats_text += f"• Total Colors: {stats.get('total_colors', 0)}\n"
        stats_text += f"• Neutral Colors: {stats.get('neutral_colors', 0)}\n"
        stats_text += f"• Vibrant Colors: {stats.get('vibrant_colors', 0)}\n"
        stats_text += f"• Avg Brightness: {stats.get('avg_brightness', 0):.2f}\n\n"
        
        # Color family distribution
        families = [c['family'] for c in colors]
        family_counts = Counter(families)
        if family_counts:
            stats_text += f" Color Families:\n"
            for family, count in family_counts.most_common(3):
                stats_text += f"• {family}: {count}\n"
        
        ax_stats.text(0.05, 0.98, stats_text,
                     transform=ax_stats.transAxes,
                     fontsize=10, va='top',
                     linespacing=1.5)
        
        # Main title
        filename = os.path.basename(image_path) if isinstance(image_path, str) else "Image"
        plt.suptitle(f'Color Extraction: {filename}', 
                    fontsize=16, fontweight='bold', y=1.02)
        
        plt.tight_layout()
        plt.show()
        
    except Exception as e:
        print(f"Error displaying image: {e}")
        
        # Fallback: simple display
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        
        if 'img' in locals():
            ax1.imshow(img_array)
            ax1.set_title('Image')
            ax1.axis('off')
        
        # Simple color display
        colors = color_result.get('colors', [])
        for i, color in enumerate(colors):
            rect = plt.Rectangle((i, 0), 1, 1, 
                               color=np.array(color['rgb'])/255.0)
            ax2.add_patch(rect)
            
            text_color = 'white' if color.get('brightness', 0.5) < 0.5 else 'black'
            ax2.text(i + 0.5, 0.5, 
                    f"{color.get('name', 'Unknown')}\n{color.get('percentage', 0):.1f}%",
                    ha='center', va='center',
                    color=text_color,
                    fontsize=8)
        
        ax2.set_xlim(0, len(colors))
        ax2.set_ylim(0, 1)
        ax2.set_title('Extracted Colors')
        ax2.axis('off')
        
        plt.tight_layout()
        plt.show()


def visualize_color_palette(color_result, title="Color Palette"):
    """Visualize extracted color palette"""
    colors = color_result['colors']
    
    # Create figure
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle(title, fontsize=16, fontweight='bold')
    
    # 1. Color Swatches
    ax1 = axes[0, 0]
    ax1.set_title('Color Swatches', fontsize=14)
    
    n_colors = len(colors)
    for i, color in enumerate(colors):
        # Create color patch
        rect = plt.Rectangle((i, 0), 1, 1, 
                           color=np.array(color['rgb'])/255.0)
        ax1.add_patch(rect)
        
        # Add text
        ax1.text(i + 0.5, 0.5, 
                f"{color['name']}\n{color['percentage']:.1f}%",
                ha='center', va='center',
                color='white' if color['brightness'] < 0.5 else 'black',
                fontsize=10, fontweight='bold')
    
    ax1.set_xlim(0, n_colors)
    ax1.set_ylim(0, 1)
    ax1.set_aspect('equal')
    ax1.axis('off')
    
    # 2. Color Information
    ax2 = axes[0, 1]
    ax2.set_title('Color Details', fontsize=14)
    ax2.axis('off')
    
    info_text = f"Dominant: {color_result['dominant_color']['name']}\n"
    info_text += f"Palette Type: {color_result['palette_type']}\n\n"
    
    for i, color in enumerate(colors[:5], 1):
        info_text += f"{i}. {color['name']}:\n"
        info_text += f"   • RGB: {color['rgb']}\n"
        info_text += f"   • HEX: {color['hex']}\n"
        info_text += f"   • Family: {color['family']}\n"
        info_text += f"   • Coverage: {color['percentage']:.1f}%\n"
        info_text += f"   • Brightness: {color['brightness']:.2f}\n"
        info_text += f"   • Saturation: {color['saturation']:.2f}\n\n"
    
    ax2.text(0.05, 0.95, info_text, 
             transform=ax2.transAxes,
             fontsize=10, va='top', linespacing=1.5)
    
    # 3. Statistics
    ax3 = axes[1, 0]
    ax3.set_title('Color Statistics', fontsize=14)
    ax3.axis('off')
    
    stats = color_result['statistics']
    stats_text = f"Total Colors: {stats['total_colors']}\n"
    stats_text += f"Neutral Colors: {stats.get('neutral_colors', 0)}\n"
    stats_text += f"Vibrant Colors: {stats.get('vibrant_colors', 0)}\n"
    stats_text += f"Light Colors: {stats.get('light_colors', 0)}\n"
    stats_text += f"Dark Colors: {stats.get('dark_colors', 0)}\n"
    stats_text += f"Avg Brightness: {stats.get('avg_brightness', 0):.2f}\n"
    stats_text += f"Avg Saturation: {stats.get('avg_saturation', 0):.2f}\n"
    
    ax3.text(0.05, 0.95, stats_text,
             transform=ax3.transAxes,
             fontsize=12, va='top', linespacing=1.8)
    
    # 4. Suggestions
    ax4 = axes[1, 1]
    ax4.set_title('Styling Suggestions', fontsize=14)
    ax4.axis('off')
    
    if color_result.get('suggestions'):
        suggestions_text = ""
        for i, suggestion in enumerate(color_result['suggestions'][:3], 1):
            suggestions_text += f"{i}. {suggestion['for_color']}:\n"
            suggestions_text += f"   {suggestion['advice']}\n"
            suggestions_text += f"   Good with: {', '.join(suggestion['good_with'][:3])}\n\n"
        
        ax4.text(0.05, 0.95, suggestions_text,
                 transform=ax4.transAxes,
                 fontsize=10, va='top', linespacing=1.5)
    
    plt.tight_layout()
    plt.show()


def display_color_extraction(image_path, extractor):
    """Display image and its color extraction results"""
    # Load and display image
    img = Image.open(image_path) if os.path.exists(image_path) else None
    if img is None:
        print(f"Image not found: {image_path}")
        return
    
    # Extract colors
    color_result = extractor.extract_from_image(image_path)
    
    # Create figure
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))
    
    # Display image
    axes[0].imshow(img)
    axes[0].set_title(f'Image: {os.path.basename(image_path)}', fontsize=14)
    axes[0].axis('off')
    
    # Display color palette
    colors = color_result['colors']
    for i, color in enumerate(colors):
        rect = plt.Rectangle((i*2, 0), 1, 1, 
                           color=np.array(color['rgb'])/255.0)
        axes[1].add_patch(rect)
        
        # Add color name and percentage
        axes[1].text(i*2 + 0.5, 0.5, 
                    f"{color['name']}\n{color['percentage']:.1f}%",
                    ha='center', va='center',
                    color='white' if color['brightness'] < 0.5 else 'black',
                    fontsize=9)
    
    axes[1].set_xlim(0, len(colors)*2)
    axes[1].set_ylim(0, 1)
    axes[1].set_title(f"Extracted Colors ({color_result['palette_type']})", fontsize=14)
    axes[1].set_aspect('equal')
    axes[1].axis('off')
    
    plt.tight_layout()
    plt.show()
    
    # Print detailed info
    print(f"\n{'='*60}")
    print(f"COLOR EXTRACTION RESULTS")
    print(f"{'='*60}")
    print(f"Image: {os.path.basename(image_path)}")
    print(f"Dominant Color: {color_result['dominant_color']['name']}")
    print(f"Palette Type: {color_result['palette_type']}")
    print(f"\nTop Colors:")
    for i, color in enumerate(color_result['colors'][:5], 1):
        print(f"  {i}. {color['name']:20} {color['hex']} {color['percentage']:5.1f}%")
    print(f"\nStatistics:")
    stats = color_result['statistics']
    for key, value in stats.items():
        if isinstance(value, (int, float)):
            print(f"  • {key}: {value}")


def display_image_colors_simple(image_path, color_result):
    """
    Simple display of image with colors
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Left: Image
    img = Image.open(image_path) if isinstance(image_path, str) else Image.fromarray(image_path)
    ax1.imshow(img)
    ax1.set_title('Original Image', fontsize=12)
    ax1.axis('off')
    
    # Right: Color palette
    ax2.set_title('Extracted Colors', fontsize=12)
    colors = color_result['colors']
    
    for i, color in enumerate(colors):
        # Color box
        rect = plt.Rectangle((i*1.2, 0), 1, 1, 
                           color=np.array(color['rgb'])/255.0,
                           edgecolor='black')
        ax2.add_patch(rect)
        
        # Text
        text_color = 'white' if color['brightness'] < 0.5 else 'black'
        ax2.text(i*1.2 + 0.5, 0.5, 
                f"{color['name']}\n{color['percentage']:.1f}%",
                ha='center', va='center',
                color=text_color, fontsize=9)
    
    ax2.set_xlim(0, len(colors)*1.2)
    ax2.set_ylim(0, 1)
    ax2.set_aspect('equal')
    ax2.axis('off')
    
    # Info text
    dominant = color_result['dominant_color']
    info_text = f"Dominant: {dominant['name']} ({dominant['hex']})\n"
    info_text += f"Palette: {color_result['palette_type']}"
    
    ax2.text(0, -0.1, info_text, transform=ax2.transAxes,
            fontsize=10, va='top')
    
    plt.tight_layout()
    plt.show()

# ============================
# 4. BATCH PROCESSING FOR KAGGLE DATASET
# ============================

def process_fashion_dataset(extractor, image_dir, sample_size=20):
    """
    Process multiple images from fashion dataset
    """
    results = []
    
    # Get list of images
    image_files = []
    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
        image_files.extend([f for f in os.listdir(image_dir) 
                          if f.lower().endswith(ext)])
    
    # Limit sample size
    if sample_size:
        image_files = image_files[:sample_size]
    
    print(f"Processing {len(image_files)} images...")
    
    for img_file in tqdm(image_files, desc="Extracting colors"):
        img_path = os.path.join(image_dir, img_file)
        
        try:
            # Extract colors
            color_result = extractor.extract_from_image(img_path)
            
            # Add filename to result
            color_result['filename'] = img_file
            color_result['success'] = True
            
            results.append(color_result)
            
        except Exception as e:
            print(f"Error processing {img_file}: {e}")
            results.append({
                'filename': img_file,
                'success': False,
                'error': str(e)
            })
    
    return results

def analyze_batch_results(results):
    """Analyze batch processing results"""
    successful = [r for r in results if r.get('success', False)]
    failed = [r for r in results if not r.get('success', False)]
    
    print(f"\n{'='*60}")
    print("BATCH PROCESSING SUMMARY")
    print(f"{'='*60}")
    print(f"Total images: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if not successful:
        return
    
    # Analyze color statistics
    all_colors = []
    palette_types = []
    
    for result in successful:
        all_colors.extend([c['name'] for c in result.get('colors', [])])
        palette_types.append(result.get('palette_type', 'Unknown'))
    
    # Most common colors
    color_counts = Counter(all_colors)
    print(f"\nMost Common Colors:")
    for color, count in color_counts.most_common(10):
        print(f"  {color}: {count} times")
    
    # Most common palette types
    palette_counts = Counter(palette_types)
    print(f"\nMost Common Palette Types:")
    for palette, count in palette_counts.most_common():
        print(f"  {palette}: {count} images")
    
    # Calculate average statistics
    avg_colors_per_image = np.mean([len(r.get('colors', [])) for r in successful])
    avg_brightness = np.mean([r['statistics'].get('avg_brightness', 0) 
                             for r in successful if 'statistics' in r])
    
    print(f"\nAverage Colors per Image: {avg_colors_per_image:.1f}")
    print(f"Average Brightness: {avg_brightness:.2f}")

# Add this at the end of color_extraction.py

def extract_colors_simple(pil_image, num_colors=3):
    """
    Simple wrapper for local app.py integration.
    
    Args:
        pil_image: PIL Image (RGBA with transparent background)
        num_colors: Number of dominant colors to extract
    
    Returns:
        dict with:
        - primary_color: str (main color name)
        - colors: list of {name, rgb, hex, percentage}
        - palette_type: str
    """
    extractor = KaggleColorExtractor(num_colors=num_colors)
    result = extractor.extract_from_image(np.array(pil_image), is_path=False)
    
    return {
        'primary_color': result['dominant_color']['name'],
        'colors': result['colors'],
        'palette_type': result['palette_type']
    }