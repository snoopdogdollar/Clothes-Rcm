"""
Clothing classification utilities for trained models.
Supports both broad categories (masterCategory) and detailed categories (articleType).
"""

import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image
from pathlib import Path
import json
import timm
from typing import Tuple, Dict, Optional


# Fashion-MNIST class names (in correct order)
FASHION_MNIST_CLASSES = [
    "T-shirt/top", "Trouser", "Pullover", "Dress", "Coat",
    "Sandal", "Shirt", "Sneaker", "Bag", "Ankle boot"
]


class ClothingClassifier:
    """
    Clothing classifier for Fashion-MNIST trained models.
    """
    
    def __init__(self, model_path, class_names_path=None, device=None):
        """
        Initialize the clothing classifier.
        
        Args:
            model_path: Path to the .pth model file
            class_names_path: Path to JSON file with class names (optional)
            device: Device to run inference on ('cuda' or 'cpu')
        """
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_path = Path(model_path)
        
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Load class names - default to Fashion-MNIST classes
        if class_names_path and Path(class_names_path).exists():
            with open(class_names_path, 'r') as f:
                self.class_names = json.load(f)
        else:
            self.class_names = FASHION_MNIST_CLASSES
        
        # Initialize model
        self.model = None
        self.num_classes = len(self.class_names)
        
        # CRITICAL: Preprocessing must match Kaggle training
        # - Resize to 224x224 (ResNet18 input size)
        # - Convert to 3-channel grayscale (RGB with identical channels)
        # - ToTensor() converts PIL [0,255] -> Tensor [0,1] automatically
        # - NO normalization (matches Kaggle training setup)
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),                # Force 224x224 (not just shortest side)
            transforms.Grayscale(num_output_channels=3),  # 3-channel grayscale
            transforms.ToTensor()                         # [0,1] normalization only
        ])
        
        # Load the model
        self._load_model()
    
    def _load_model(self):
        """Load the pre-trained Fashion-MNIST model from .pth file."""
        try:
            # Load checkpoint
            checkpoint = torch.load(self.model_path, map_location=self.device)
            
            # Extract state dict
            if isinstance(checkpoint, dict):
                if 'model_state_dict' in checkpoint:
                    state_dict = checkpoint['model_state_dict']
                    self.num_classes = checkpoint.get('num_classes', len(self.class_names))
                elif 'state_dict' in checkpoint:
                    state_dict = checkpoint['state_dict']
                    self.num_classes = checkpoint.get('num_classes', len(self.class_names))
                else:
                    state_dict = checkpoint
            else:
                state_dict = checkpoint
            
            # Use exact architecture from Kaggle training
            # ResNet18 as feature extractor + custom classifier for Fashion-MNIST
            
            # Architecture from Kaggle training: ResNet18 feature extractor + custom classifier
            class FashionMNISTCNN(nn.Module):
                def __init__(self, num_classes=7):
                    super(FashionMNISTCNN, self).__init__()
                    # Use ResNet18 as base model (matches Kaggle training)
                    self.base_model = timm.create_model('resnet18', pretrained=True, num_classes=num_classes)
                    self.features = nn.Sequential(*list(self.base_model.children())[:-1])
                    enet_out_size = 512
                    # Custom classifier head
                    self.classifier = nn.Linear(enet_out_size, num_classes)
                
                def forward(self, x):
                    x = self.features(x)
                    x = x.view(x.size(0), -1)  # Flatten
                    output = self.classifier(x)
                    return output
            
            self.model = FashionMNISTCNN(num_classes=self.num_classes)
            
            # Load state dict
            self.model.load_state_dict(state_dict, strict=False)
            self.model.to(self.device)
            self.model.eval()  # Set to evaluation mode
            
            print(f"Model loaded successfully from {self.model_path}")
            print(f"Number of classes: {self.num_classes}")
            print(f"Class names: {self.class_names}")
            print(f"Device: {self.device}")
            
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {str(e)}")
    
    def classify(self, image):
        """
        Classify a clothing item from an image.
        
        Args:
            image: PIL Image (RGB or grayscale) - segmented clothing item
        
        Returns:
            tuple: (predicted_class_name, confidence_score, all_predictions)
        """
        # Preprocess image - converts to 3-channel grayscale, resizes to 224x224, normalizes to [0,1]
        input_tensor = self.transform(image).unsqueeze(0).to(self.device)
        
        # Safety check: ensure correct shape (batch_size, channels, height, width)
        expected_shape = (1, 3, 224, 224)
        if input_tensor.shape != expected_shape:
            raise ValueError(
                f"Input tensor shape mismatch! Expected {expected_shape}, got {input_tensor.shape}"
            )
        
        print(f"  Input tensor shape: {input_tensor.shape} (correct for ResNet18)")
        
        # Run inference with no gradient computation
        with torch.no_grad():
            self.model.eval()  # Ensure model is in eval mode
            outputs = self.model(input_tensor)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
            top_prob, top_idx = torch.topk(probabilities, 1)
        
        # Get class name
        predicted_idx = top_idx[0].item()
        predicted_class = self.class_names[predicted_idx]
        confidence = float(top_prob[0].item())
        
        # Get top 3 predictions
        top3_prob, top3_idx = torch.topk(probabilities, min(3, self.num_classes))
        all_predictions = []
        for prob, idx in zip(top3_prob, top3_idx):
            class_name = self.class_names[idx.item()]
            all_predictions.append((class_name, float(prob.item())))
        
        return predicted_class, confidence, all_predictions


# Global classifier instance (lazy loading)
_classifier = None


def get_classifier(model_path=None, class_names_path=None):
    """
    Get or initialize the global classifier instance.
    
    Args:
        model_path: Path to .pth model file (required on first call)
        class_names_path: Path to JSON file with class names
    
    Returns:
        ClothingClassifier instance
    """
    global _classifier
    
    if _classifier is None:
        if model_path is None:
            # Try default location
            default_path = Path(__file__).parent.parent / 'models' / 'clothing_classifier.pth'
            if default_path.exists():
                model_path = default_path
            else:
                raise ValueError(
                    "No model path provided and default model not found.\n"
                    "Please provide model_path or place model at: models/clothing_classifier.pth"
                )
        _classifier = ClothingClassifier(model_path, class_names_path)
    
    return _classifier


def classify_clothing(image, model_path=None, class_names_path=None):
    """
    Classify clothing type from segmented image.
    
    Args:
        image: PIL Image - segmented clothing item
        model_path: Path to .pth model file (optional if already initialized)
        class_names_path: Path to JSON file with class names (optional)
    
    Returns:
        tuple: (predicted_category, confidence_score, top3_predictions)
    """
    classifier = get_classifier(model_path, class_names_path)
    predicted_class, confidence, top3 = classifier.classify(image)
    return predicted_class, confidence, top3