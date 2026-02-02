"""
Kaggle Training Template for Clothing Classification on articleType
Train a ResNet model to predict detailed clothing categories from styles.csv

Steps to use this in Kaggle:
1. Upload the Fashion Product Images dataset (contains images/ folder and styles.csv)
2. Copy this code into a Kaggle notebook
3. Run the training - it will automatically extract articleType categories from styles.csv
4. Download the trained model (clothing_classifier.pth) and class_names.json
5. Place them in your local models/ folder
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import models, transforms
from PIL import Image
import pandas as pd
from pathlib import Path
import json

# Dataset class for Fashion Product Images
class ClothingDataset(Dataset):
    def __init__(self, styles_csv, image_dir, transform=None, label_column='articleType'):
        """
        Dataset for Fashion Product Images from Kaggle.
        
        Args:
            styles_csv: Path to styles.csv (contains id, articleType, etc.)
            image_dir: Path to images folder (images are named {id}.jpg)
            transform: PyTorch transforms
            label_column: Which column to use as labels (default: 'articleType' for detailed categories)
        """
        # Load styles.csv
        self.data = pd.read_csv(styles_csv, on_bad_lines='skip')
        
        # Filter out rows with missing articleType
        self.data = self.data[self.data[label_column].notna()].copy()
        
        # Create label mapping (articleType -> integer)
        unique_labels = sorted(self.data[label_column].unique())
        self.label_to_idx = {label: idx for idx, label in enumerate(unique_labels)}
        self.idx_to_label = {idx: label for label, idx in self.label_to_idx.items()}
        
        # Add numeric label column
        self.data['label_idx'] = self.data[label_column].map(self.label_to_idx)
        
        # Filter to only rows where image file exists
        self.image_dir = Path(image_dir)
        self.data = self.data[self.data['id'].apply(
            lambda x: (self.image_dir / f"{x}.jpg").exists()
        )].copy()
        
        self.transform = transform
        print(f"Dataset: {len(self.data)} images across {len(unique_labels)} categories")
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        row = self.data.iloc[idx]
        img_id = row['id']
        img_path = self.image_dir / f"{img_id}.jpg"
        
        image = Image.open(img_path).convert('RGB')
        label = int(row['label_idx'])
        
        if self.transform:
            image = self.transform(image)
        
        return image, label
    
    def get_class_names(self):
        """Return list of class names in order"""
        return [self.idx_to_label[i] for i in range(len(self.idx_to_label))]

# Training function
def train_model(model, train_loader, val_loader, num_epochs=10, device='cuda'):
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    best_val_acc = 0.0
    
    for epoch in range(num_epochs):
        # Training phase
        model.train()
        train_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
        
        # Validation phase
        model.eval()
        val_correct = 0
        val_total = 0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                _, predicted = torch.max(outputs.data, 1)
                val_total += labels.size(0)
                val_correct += (predicted == labels).sum().item()
        
        val_acc = 100 * val_correct / val_total
        print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {train_loss/len(train_loader):.4f}, Val Acc: {val_acc:.2f}%')
        
        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save({
                'model_state_dict': model.state_dict(),
                'num_classes': model.fc.out_features,
                'class_names': class_names,  # Define your class names
                'val_acc': val_acc
            }, 'clothing_classifier.pth')
    
    return model

# Main training code
if __name__ == '__main__':
    # Paths in Kaggle environment
    styles_csv = '/kaggle/input/fashion-product-images-dataset/styles.csv'
    images_dir = '/kaggle/input/fashion-product-images-dataset/images'
    
    # Data transforms (no normalization - matches inference in app.py)
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(10),
        transforms.Grayscale(num_output_channels=3),  # 3-channel grayscale
        transforms.ToTensor()  # [0,1] normalization only
    ])
    
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.Grayscale(num_output_channels=3),
        transforms.ToTensor()
    ])
    
    # Load full dataset
    full_dataset = ClothingDataset(styles_csv, images_dir, train_transform, label_column='articleType')
    class_names = full_dataset.get_class_names()
    
    print(f"\nTraining on {len(class_names)} articleType categories:")
    for i, name in enumerate(class_names[:10]):  # Show first 10
        print(f"  {i}: {name}")
    if len(class_names) > 10:
        print(f"  ... and {len(class_names) - 10} more")
    
    # Split into train/val (80/20)
    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(
        full_dataset, [train_size, val_size]
    )
    
    # Apply validation transform to val_dataset
    val_dataset.dataset.transform = val_transform
    
    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False, num_workers=2)
    
    # Create model
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = models.resnet18(pretrained=True)  # ResNet18 (matches app.py architecture)
    model.fc = nn.Linear(model.fc.in_features, len(class_names))
    model = model.to(device)
    
    print(f"\nTraining on {device}...")
    
    # Train
    train_model(model, train_loader, val_loader, num_epochs=10, device=device)
    
    # Save class names
    with open('class_names.json', 'w') as f:
        json.dump(class_names, f, indent=2)
    
    print("\n✓ Training complete!")
    print("Download these files:")
    print("  - clothing_classifier.pth")
    print("  - class_names.json")
    print("Place them in your local models/ folder")