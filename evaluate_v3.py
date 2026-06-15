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
import cv2
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, ConfusionMatrixDisplay

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

def main(args):
    # 1. Setup Models
    cnn_model = load_efficientnet(args.model_path)
    reflection_analyzer = CornealReflectionAnalyzer()
    
    # Load Fusion Classifier
    print(f"Loading Fusion Model from {args.fusion_model}...")
    fusion_clf = joblib.load(args.fusion_model)
    
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
    
    for img_path, label in tqdm(image_files, desc="Eval V3"):
        try:
            # A. CNN Score
            img = Image.open(img_path).convert('RGB')
            img_t = transform(img).unsqueeze(0).to(DEVICE)
            with torch.no_grad():
                logits = cnn_model(img_t)
                cnn_fake_prob = torch.sigmoid(logits).item()
            
            # B. Reflection Score
            reflection_consistency = reflection_analyzer.calculate_consistency_score(img_path)
            reflection_fake_prob = 1.0 - reflection_consistency
            
            # C. Trained Fusion
            # Input format: [[cnn_prob, reflection_prob]]
            features = np.array([[cnn_fake_prob, reflection_fake_prob]])
            
            # Predict Probability of Fake
            fusion_fake_prob = fusion_clf.predict_proba(features)[0][1]
            prediction = 1 if fusion_fake_prob > 0.5 else 0
            
            y_true.append(label)
            y_pred_fusion.append(prediction)
            y_prob_fusion.append(fusion_fake_prob)
            
            results.append({
                'filename': os.path.basename(img_path),
                'true_label': 'Fake' if label==1 else 'Real',
                'cnn_fake_prob': cnn_fake_prob,
                'reflection_consistency': reflection_consistency,
                'fusion_fake_prob': fusion_fake_prob,
                'prediction': 'Fake' if prediction==1 else 'Real',
                'correct': prediction == label
            })
        except Exception as e:
            print(f"Error processing {img_path}: {e}")

    # 4. Metrics & Saving
    df = pd.DataFrame(results)
    df.to_csv(os.path.join(args.output_dir, 'fusion_v3_predictions.csv'), index=False)
    
    acc = accuracy_score(y_true, y_pred_fusion)
    prec = precision_score(y_true, y_pred_fusion)
    rec = recall_score(y_true, y_pred_fusion)
    f1 = f1_score(y_true, y_pred_fusion)
    auc = roc_auc_score(y_true, y_prob_fusion)
    
    print("\n--- Fusion V3 (Trained) Results ---")
    print(f"Accuracy : {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall   : {rec:.4f}")
    print(f"F1-Score : {f1:.4f}")
    print(f"ROC-AUC  : {auc:.4f}")
    
    # Confusion Matrix
    cm = confusion_matrix(y_true, y_pred_fusion)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['Real', 'Fake'])
    disp.plot(cmap=plt.cm.Greens)
    plt.title("Trained Fusion (V3) Confusion Matrix")
    plt.savefig(os.path.join(args.output_dir, 'confusion_matrix_v3.png'))
    
    # Save Metrics
    with open(os.path.join(args.output_dir, 'metrics_v3.txt'), 'w') as f:
        f.write(f"Accuracy: {acc:.4f}\n")
        f.write(f"Precision: {prec:.4f}\n")
        f.write(f"Recall: {rec:.4f}\n")
        f.write(f"F1-Score: {f1:.4f}\n")
        f.write(f"ROC-AUC: {auc:.4f}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--test_dir', default='dataset_split/test', help='Path to test set')
    parser.add_argument('--model_path', default='outputs/efficientnet/best_model.pth', help='Path to trained .pth model')
    parser.add_argument('--fusion_model', default='outputs/fusion_v3/fusion_model.pkl', help='Path to trained fusion model')
    parser.add_argument('--output_dir', default='outputs/fusion_v3', help='Output directory')
    args = parser.parse_args()
    
    main(args)
