import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import numpy as np
import os
import argparse
import pandas as pd
from tqdm import tqdm
import cv2
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, ConfusionMatrixDisplay

# Import custom module
from corneal_reflection import CornealReflectionAnalyzer

# Configuration
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
IMG_SIZE = 224

def load_efficientnet(model_path):
    print(f"Loading EfficientNet from {model_path}...")
    # Re-instantiate architecture to load weights
    model = models.efficientnet_b0(pretrained=False)
    num_ftrs = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(num_ftrs, 1)
    
    # Load state dict
    try:
        # Check if full model or state_dict
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

def predict_cnn(model, image_path, transform):
    try:
        img = Image.open(image_path).convert('RGB')
        img_t = transform(img).unsqueeze(0).to(DEVICE)
        
        with torch.no_grad():
            logits = model(img_t)
            prob = torch.sigmoid(logits).item()
            return prob # Probability of being Fake (1)
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return 0.5

def main(args):
    # 1. Setup Models
    cnn_model = load_efficientnet(args.model_path)
    reflection_analyzer = CornealReflectionAnalyzer()
    
    transform = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    # 2. Prepare Data
    test_dir = args.test_dir
    results = []
    
    real_path = os.path.join(test_dir, 'real')
    fake_path = os.path.join(test_dir, 'fake')
    
    image_files = []
    #Tuples: (path, true_label) -> 0=Real, 1=Fake
    if os.path.exists(real_path):
        image_files.extend([(os.path.join(real_path, f), 0) for f in os.listdir(real_path) if f.lower().endswith(('.jpg', '.png'))])
    if os.path.exists(fake_path):
        image_files.extend([(os.path.join(fake_path, f), 1) for f in os.listdir(fake_path) if f.lower().endswith(('.jpg', '.png'))])
        
    print(f"Found {len(image_files)} test images.")
    
    # 3. Inference Loop
    y_true = []
    y_pred_fusion = []
    y_prob_fusion = []
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    for img_path, label in tqdm(image_files, desc="Eval"):
        # A. CNN Score (Probability of FAKE)
        cnn_fake_prob = predict_cnn(cnn_model, img_path, transform)
        
        # B. Reflection Score (Consistency -> 1.0=Real, 0.0=Fake)
        # Note: If no face found, returns 0.5 (neutral)
        reflection_consistency = reflection_analyzer.calculate_consistency_score(img_path)
        
        # C. Attention-Based Dynamic Fusion Weighting
        if abs(reflection_consistency - 0.5) < 1e-5:
            # Physics is neutral/uncertain (e.g. eyes closed, sunglasses, no face)
            # Dynamic weights: CNN gets 100% influence, physics check is ignored
            w_cnn = 1.0
            w_ref = 0.0
            reflection_fake_prob = 0.5
        else:
            # Physics is active and confident (eyes open and highlights extracted)
            # Dynamic weights: CNN gets 60%, physics check gets 40% (high confidence sanity gate)
            w_cnn = 0.6
            w_ref = 0.4
            reflection_fake_prob = 1.0 - reflection_consistency
            
        final_fake_score = (w_cnn * cnn_fake_prob) + (w_ref * reflection_fake_prob)
        prediction = 1 if final_fake_score > 0.5 else 0
        
        y_true.append(label)
        y_pred_fusion.append(prediction)
        y_prob_fusion.append(final_fake_score)
        
        results.append({
            'filename': os.path.basename(img_path),
            'true_label': 'Fake' if label==1 else 'Real',
            'cnn_fake_prob': cnn_fake_prob,
            'reflection_consistency': reflection_consistency,
            'fusion_fake_score': final_fake_score,
            'prediction': 'Fake' if prediction==1 else 'Real',
            'correct': prediction == label
        })

    # 4. Metrics & Saving
    df = pd.DataFrame(results)
    df.to_csv(os.path.join(args.output_dir, 'fusion_predictions.csv'), index=False)
    
    acc = accuracy_score(y_true, y_pred_fusion)
    prec = precision_score(y_true, y_pred_fusion)
    rec = recall_score(y_true, y_pred_fusion)
    f1 = f1_score(y_true, y_pred_fusion)
    auc = roc_auc_score(y_true, y_prob_fusion)
    
    print("\n--- Fusion Results ---")
    print(f"Accuracy : {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall   : {rec:.4f}")
    print(f"F1-Score : {f1:.4f}")
    print(f"ROC-AUC  : {auc:.4f}")
    
    # Confusion Matrix
    cm = confusion_matrix(y_true, y_pred_fusion)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['Real', 'Fake'])
    disp.plot(cmap=plt.cm.Blues)
    plt.title("Fusion Model Confusion Matrix")
    plt.savefig(os.path.join(args.output_dir, 'confusion_matrix.png'))
    
    # Save Metrics
    with open(os.path.join(args.output_dir, 'metrics.txt'), 'w') as f:
        f.write(f"Accuracy: {acc:.4f}\n")
        f.write(f"Precision: {prec:.4f}\n")
        f.write(f"Recall: {rec:.4f}\n")
        f.write(f"F1-Score: {f1:.4f}\n")
        f.write(f"ROC-AUC: {auc:.4f}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--test_dir', default='dataset_split/test', help='Path to test set')
    parser.add_argument('--model_path', default='outputs/efficientnet/best_model.pth', help='Path to trained .pth model')
    parser.add_argument('--output_dir', default='outputs/fusion', help='Output directory')
    args = parser.parse_args()
    
    main(args)
