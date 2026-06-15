import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import numpy as np
import os
import argparse
import pandas as pd
from tqdm import tqdm
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report

# Import custom modules
from corneal_reflection import CornealReflectionAnalyzer

# Configuration
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
IMG_SIZE = 224

def load_efficientnet(model_path):
    print(f"Loading EfficientNet from {model_path}...")
    model = models.efficientnet_b0(pretrained=False)
    num_ftrs = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(num_ftrs, 1)
    
    try:
        checkpoint = torch.load(model_path, map_location=DEVICE)
        if isinstance(checkpoint, dict):
            model.load_state_dict(checkpoint)
        else:
            model = checkpoint
    except Exception as e:
        print(f"Error loading model: {e}")
        return None
        
    model = model.to(DEVICE)
    model.eval()
    return model

def extract_features(cnn_model, reflection_analyzer, data_dir, split_name):
    """
    Extracts [cnn_prob, reflection_score] for all images in a split.
    Returns X (features) and y (labels).
    """
    transform = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    features = []
    labels = []
    
    split_dir = os.path.join(data_dir, split_name)
    real_path = os.path.join(split_dir, 'real')
    fake_path = os.path.join(split_dir, 'fake')
    
    image_files = []
    if os.path.exists(real_path):
        image_files.extend([(os.path.join(real_path, f), 0) for f in os.listdir(real_path) if f.lower().endswith(('.jpg', '.png'))])
    if os.path.exists(fake_path):
        image_files.extend([(os.path.join(fake_path, f), 1) for f in os.listdir(fake_path) if f.lower().endswith(('.jpg', '.png'))])
    
    print(f"Extracting features from {len(image_files)} images in '{split_name}'...")
    
    for img_path, label in tqdm(image_files, desc=f"Extracting {split_name}"):
        try:
            # 1. CNN Feature
            img = Image.open(img_path).convert('RGB')
            img_t = transform(img).unsqueeze(0).to(DEVICE)
            with torch.no_grad():
                logits = cnn_model(img_t)
                cnn_prob = torch.sigmoid(logits).item()
            
            # 2. Reflection Feature (Consistency)
            # We want "Fake Probability" for the feature to align with CNN
            # So feature = 1.0 - consistency
            consistency = reflection_analyzer.calculate_consistency_score(img_path)
            reflection_fake_prob = 1.0 - consistency
            
            features.append([cnn_prob, reflection_fake_prob])
            labels.append(label)
        except Exception as e:
            print(f"Error processing {img_path}: {e}")
            
    return np.array(features), np.array(labels)

def main(args):
    # 1. Load Models
    cnn_model = load_efficientnet(args.cnn_model)
    reflection = CornealReflectionAnalyzer()
    
    # 2. Extract Features (Train & Val)
    # We use both to train the fusion classifier to have enough data
    X_train, y_train = extract_features(cnn_model, reflection, args.data_dir, 'train')
    X_val, y_val = extract_features(cnn_model, reflection, args.data_dir, 'val')
    
    # Combine
    X_full = np.concatenate((X_train, X_val))
    y_full = np.concatenate((y_train, y_val))
    
    # 3. Train Logistic Regression
    print("Training Fusion Meta-Classifier (Logistic Regression)...")
    clf = LogisticRegression(random_state=42)
    clf.fit(X_full, y_full)
    
    # 4. Coefficients
    print(f"Intercept: {clf.intercept_[0]:.4f}")
    print(f"Coefficients: CNN={clf.coef_[0][0]:.4f}, Reflection={clf.coef_[0][1]:.4f}")
    
    # Save feature importance interpretation
    norm_coef = np.abs(clf.coef_[0]) / np.sum(np.abs(clf.coef_[0]))
    print(f"Relative Importance -> CNN: {norm_coef[0]:.1%}, Reflection: {norm_coef[1]:.1%}")
    
    # 5. Save
    os.makedirs(args.output_dir, exist_ok=True)
    joblib.dump(clf, os.path.join(args.output_dir, 'fusion_model.pkl'))
    print(f"Saved fusion model to {args.output_dir}/fusion_model.pkl")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', default='dataset_split', help='Path to dataset split')
    parser.add_argument('--cnn_model', default='outputs/efficientnet/best_model.pth', help='Path to trained EfficientNet')
    parser.add_argument('--output_dir', default='outputs/fusion_v3', help='Output directory')
    args = parser.parse_args()
    
    main(args)
