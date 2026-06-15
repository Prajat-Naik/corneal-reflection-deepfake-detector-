import os
import time
import argparse
import copy
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms
from PIL import Image
import mediapipe as mp
import cv2
import numpy as np
from tqdm import tqdm
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, classification_report

# --- Configuration ---
IMG_SIZE = 224
BATCH_SIZE = 16
LEARNING_RATE = 1e-4
NUM_EPOCHS = 20
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {DEVICE}")

# --- MediaPipe Init ---
mp_face_detection = mp.solutions.face_detection
face_detection = mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5)

# --- Dataset Class ---
class DeepfakeDataset(Dataset):
    def __init__(self, root_dir, split='train', transform=None, crop_face=True):
        """
        Args:
            root_dir (str): Root directory (e.g., 'dataset_split')
            split (str): 'train', 'val', or 'test'
            transform (callable, optional): Transform to apply
            crop_face (bool): Whether to use MediaPipe to crop face
        """
        self.root_dir = root_dir
        self.split = split
        self.transform = transform
        self.crop_face = crop_face
        self.image_paths = []
        self.labels = [] # 0: Real, 1: Fake (Standard: Real=0, Fake=1)
        
        # Load Real (Label 0)
        real_dir = os.path.join(root_dir, split, 'real')
        if os.path.exists(real_dir):
            for fname in os.listdir(real_dir):
                if fname.lower().endswith(('.png', '.jpg', '.jpeg')):
                    self.image_paths.append(os.path.join(real_dir, fname))
                    self.labels.append(0) 

        # Load Fake (Label 1)
        fake_dir = os.path.join(root_dir, split, 'fake')
        if os.path.exists(fake_dir):
            for fname in os.listdir(fake_dir):
                if fname.lower().endswith(('.png', '.jpg', '.jpeg')):
                    self.image_paths.append(os.path.join(fake_dir, fname))
                    self.labels.append(1)
        
        print(f"Loaded {len(self.image_paths)} images for {split} split.")

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        label = self.labels[idx]
        
        try:
            # Face Detection & Cropping
            if self.crop_face:
                image_cv = cv2.imread(img_path)
                if image_cv is not None:
                    image_rgb = cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB)
                    results = face_detection.process(image_rgb)
                    
                    if results.detections:
                        # Crop the first detected face
                        detection = results.detections[0]
                        bboxC = detection.location_data.relative_bounding_box
                        ih, iw, _ = image_rgb.shape
                        x, y, w, h = int(bboxC.xmin * iw), int(bboxC.ymin * ih), \
                                     int(bboxC.width * iw), int(bboxC.height * ih)
                        
                        # Add padding
                        pad = int(w * 0.1) 
                        x = max(0, x - pad)
                        y = max(0, y - pad)
                        w = min(iw - x, w + 2*pad)
                        h = min(ih - y, h + 2*pad)
                        
                        face_crop = image_rgb[y:y+h, x:x+w]
                        if face_crop.size > 0:
                            image = Image.fromarray(face_crop)
                        else:
                            image = Image.fromarray(image_rgb) # Fallback
                    else:
                        image = Image.fromarray(image_rgb) # Fallback if no face
                else: 
                     # Should not happen if paths are correct
                     image = Image.new('RGB', (IMG_SIZE, IMG_SIZE))
            else:
                 image = Image.open(img_path).convert('RGB')

        except Exception:
            # Fallback for corrupt images
            print(f"Error loading {img_path}")
            image = Image.new('RGB', (IMG_SIZE, IMG_SIZE))

        if self.transform:
            image = self.transform(image)
            
        return image, label

# --- Transforms ---
data_transforms = {
    'train': transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(10),
        transforms.ColorJitter(brightness=0.1, contrast=0.1),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
    'val': transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
    'test': transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
}

def train_model(model, dataloaders, criterion, optimizer, num_epochs=20, output_dir='outputs/efficientnet'):
    since = time.time()
    best_model_wts = copy.deepcopy(model.state_dict())
    best_f1 = 0.0
    
    os.makedirs(output_dir, exist_ok=True)
    
    history = {'train_loss': [], 'val_loss': [], 'val_acc': [], 'val_f1': []}

    for epoch in range(num_epochs):
        print(f'Epoch {epoch+1}/{num_epochs}')
        print('-' * 10)

        for phase in ['train', 'val']:
            if phase == 'train':
                model.train() 
            else:
                model.eval()

            running_loss = 0.0
            running_corrects = 0
            all_labels = []
            all_preds = []

            # Iterate over data
            for inputs, labels in tqdm(dataloaders[phase], desc=phase):
                inputs = inputs.to(DEVICE)
                labels = labels.to(DEVICE).float().unsqueeze(1) # BCE needs float labels [N, 1]

                optimizer.zero_grad()

                with torch.set_grad_enabled(phase == 'train'):
                    outputs = model(inputs)
                    loss = criterion(outputs, labels)
                    preds = torch.sigmoid(outputs) > 0.5 

                    if phase == 'train':
                        loss.backward()
                        optimizer.step()

                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)
                
                all_labels.extend(labels.cpu().numpy())
                all_preds.extend(preds.cpu().numpy())

            epoch_loss = running_loss / len(dataloaders[phase].dataset)
            epoch_acc = accuracy_score(all_labels, all_preds)
            epoch_f1 = f1_score(all_labels, all_preds)

            print(f'{phase} Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f} F1: {epoch_f1:.4f}')
            
            if phase == 'train':
                history['train_loss'].append(epoch_loss)
            else:
                history['val_loss'].append(epoch_loss)
                history['val_acc'].append(epoch_acc)
                history['val_f1'].append(epoch_f1)

                # deep copy the model if it's the best F1
                if epoch_f1 > best_f1:
                    best_f1 = epoch_f1
                    best_model_wts = copy.deepcopy(model.state_dict())
                    torch.save(model.state_dict(), os.path.join(output_dir, 'best_model.pth'))
                    print("  -> New Best Model Saved!")

        print()

    time_elapsed = time.time() - since
    print(f'Training complete in {time_elapsed // 60:.0f}m {time_elapsed % 60:.0f}s')
    print(f'Best Val F1: {best_f1:.4f}')

    # Load best model weights
    model.load_state_dict(best_model_wts)
    return model

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', default='dataset_split', help='Path to dataset split')
    parser.add_argument('--epochs', type=int, default=20)
    args = parser.parse_args()

    # Data Loaders
    image_datasets = {x: DeepfakeDataset(args.data_dir, x, data_transforms[x]) 
                      for x in ['train', 'val', 'test']}
    dataloaders = {x: DataLoader(image_datasets[x], batch_size=BATCH_SIZE, shuffle=(x=='train'), num_workers=0) # Windows uses 0 workers usually
                   for x in ['train', 'val', 'test']}

    # Model: EfficientNet-B0
    model = models.efficientnet_b0(pretrained=True)
    
    # Modify Classifier Layer for Binary Classification
    # EfficientNet-B0 has 'classifier' as the last layer: Sequential(Dropout, Linear)
    num_ftrs = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(num_ftrs, 1) # Output 1 logits for BCE
    
    model = model.to(DEVICE)

    criterion = nn.BCEWithLogitsLoss()
    optimizer = optim.AdamW(model.parameters(), lr=LEARNING_RATE)

    # Train
    model = train_model(model, dataloaders, criterion, optimizer, num_epochs=args.epochs)
    
    # Save Final Full Model
    torch.save(model, 'outputs/efficientnet/final_full_model.pth')
