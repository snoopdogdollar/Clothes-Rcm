"""
Kaggle Training Template for Clothing Classification
Save this as a Kaggle notebook and use it to train your model.
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

# Dataset class
class ClothingDataset(Dataset):
    def __init__(self, csv_file, image_dir, transform=None):
        self.data = pd.read_csv(csv_file)
        self.image_dir = Path(image_dir)
        self.transform = transform
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        img_path = self.image_dir / self.data.iloc[idx]['image_path']
        image = Image.open(img_path).convert('RGB')
        label = self.data.iloc[idx]['label']
        
        if self.transform:
            image = self.transform(image)
        
        return image, label

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
    # Define your class names
    class_names = ['T-shirt', 'Shirt', 'Jacket', 'Dress', 'Pants', 
                   'Shorts', 'Skirt', 'Sweater', 'Hat', 'Shoes', 'Bag']
    
    # Data transforms
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(10),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    # Load datasets
    train_dataset = ClothingDataset('train.csv', 'train_images', train_transform)
    val_dataset = ClothingDataset('val.csv', 'val_images', val_transform)
    
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)
    
    # Create model
    model = models.resnet50(pretrained=True)
    model.fc = nn.Linear(model.fc.in_features, len(class_names))
    model = model.to('cuda')
    
    # Train
    train_model(model, train_loader, val_loader, num_epochs=20)
    
    # Save class names
    with open('class_names.json', 'w') as f:
        json.dump(class_names, f)