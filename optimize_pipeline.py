import os
import cv2
import numpy as np
import json
import joblib
from skimage import feature
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Custom imports
from backend.src.face_detection import FaceDetector
from backend.src.eye_detection import EyeDetector
from backend.src.reflection_extractor import SpecularReflectionExtractor
from backend.src.metrics_calculator import MetricsCalculator

def compute_lbp_feature(image, radius=3, n_points=24):
    """Compute Uniform Local Binary Pattern histogram for face texture."""
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    try:
        lbp = feature.local_binary_pattern(gray, n_points, radius, method="uniform")
        (hist, _) = np.histogram(lbp.ravel(), bins=np.arange(0, n_points + 3), range=(0, n_points + 2))
        hist = hist.astype("float")
        hist /= (hist.sum() + 1e-7)
        return hist
    except Exception as e:
        print(f"LBP Error: {e}")
        return np.zeros(n_points + 2)

def extract_features_and_crcs(data_dir, split_name, face_detector, eye_detector, reflection_extractor, metrics_calculator):
    """
    Extracts LBP histograms and CRCS for all images in a split.
    """
    split_dir = os.path.join(data_dir, split_name)
    real_dir = os.path.join(split_dir, 'real')
    fake_dir = os.path.join(split_dir, 'fake')
    
    image_files = []
    if os.path.exists(real_dir):
        image_files.extend([(os.path.join(real_dir, f), 1) for f in os.listdir(real_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))])
    if os.path.exists(fake_dir):
        image_files.extend([(os.path.join(fake_dir, f), 0) for f in os.listdir(fake_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))])
        
    print(f"Loading {split_name} data (found {len(image_files)} images)...")
    
    features = []
    labels = []
    crcs_scores = []
    skipped_count = 0
    
    for img_path, label in image_files:
        image = cv2.imread(img_path)
        if image is None:
            continue
            
        # 1. Face Bounding Box & Crop
        face_ok, face_res = face_detector.detect_face(image)
        if not face_ok:
            # Fallback if no face detected: use resized original image
            face_crop = cv2.resize(image, (512, 512))
        else:
            face_crop = cv2.resize(face_res["crop"], (512, 512))
            
        # Compute LBP histogram
        lbp_feat = compute_lbp_feature(face_crop)
        
        # 2. Eye Specular Highlights & CRCS
        crcs = 50.0 # Default fallback
        try:
            eye_ok, eye_res = eye_detector.detect_and_crop_eyes(image)
            if eye_ok:
                l_img = eye_res["left_img"]
                r_img = eye_res["right_img"]
                l_mask = eye_res["left_mask"]
                r_mask = eye_res["right_mask"]
                
                l_refl_mask, l_blobs = reflection_extractor.extract_highlights(l_img, l_mask)
                r_refl_mask, r_blobs = reflection_extractor.extract_highlights(r_img, r_mask)
                
                l_primary = l_blobs[0] if len(l_blobs) > 0 else None
                r_primary = r_blobs[0] if len(r_blobs) > 0 else None
                
                l_size = (l_img.shape[1], l_img.shape[0])
                r_size = (r_img.shape[1], r_img.shape[0])
                
                rsi, rsi_breakdown = metrics_calculator.calculate_rsi(l_primary, r_primary, l_size, r_size)
                crcs = metrics_calculator.calculate_crcs(
                    rsi, rsi_breakdown["position"], rsi_breakdown["brightness"], rsi_breakdown["distance_mismatch"]
                )
        except Exception as e:
            pass
            
        features.append(lbp_feat)
        crcs_scores.append(crcs)
        labels.append(label)
        
    return np.array(features), np.array(crcs_scores), np.array(labels)

def main():
    data_dir = 'dataset_split'
    
    face_detector = FaceDetector()
    eye_detector = EyeDetector()
    reflection_extractor = SpecularReflectionExtractor()
    metrics_calculator = MetricsCalculator()
    
    # 1. Load and Extract Training Set
    X_train_lbp, _, y_train = extract_features_and_crcs(
        data_dir, 'train', face_detector, eye_detector, reflection_extractor, metrics_calculator
    )
    
    # 2. Train Texture SVM
    print("Training Face Texture SVM model on train split...")
    texture_clf = SVC(kernel="rbf", C=1.0, gamma='scale', probability=True, random_state=42)
    texture_clf.fit(X_train_lbp, y_train)
    
    # Save texture model to root directory and backup folder
    joblib.dump(texture_clf, 'texture_model.pkl')
    print("Saved trained texture model to root 'texture_model.pkl'")
    
    # 3. Load and Extract Validation Set
    X_val_lbp, val_crcs, y_val = extract_features_and_crcs(
        data_dir, 'val', face_detector, eye_detector, reflection_extractor, metrics_calculator
    )
    
    # Get Texture Authenticity Scores for Validation Set
    # Class 1 is Real
    val_tex_scores = texture_clf.predict_proba(X_val_lbp)[:, 1]
    
    # 4. Grid Search Weights to Optimize Fusion Accuracy
    best_acc = 0.0
    best_w_tex = 0.6
    best_w_crcs = 0.4
    
    print("\nGrid-searching weights on validation set...")
    # Search w_tex from 0.0 to 1.0 with 0.02 increments
    for w in np.linspace(0.0, 1.0, 51):
        w_tex = w
        w_crcs = 1.0 - w
        
        # Combined score = w_tex * texture_score + w_crcs * (crcs / 100.0)
        combined_scores = w_tex * val_tex_scores + w_crcs * (val_crcs / 100.0)
        preds = (combined_scores >= 0.5).astype(int)
        
        acc = accuracy_score(y_val, preds)
        if acc > best_acc:
            best_acc = acc
            best_w_tex = float(w_tex)
            best_w_crcs = float(w_crcs)
            
    print(f"Optimal weights found -> w_texture: {best_w_tex:.2f}, w_crcs: {best_w_crcs:.2f}")
    print(f"Validation Set Accuracy with optimized weights: {best_acc:.2%}")
    
    # Save weights to json file
    os.makedirs('outputs/fusion_v3', exist_ok=True)
    weights_path = 'outputs/fusion_v3/fusion_weights.json'
    with open(weights_path, 'w') as f:
        json.dump({'w_tex': best_w_tex, 'w_crcs': best_w_crcs}, f, indent=4)
    print(f"Saved optimized weights to {weights_path}")
    
    # 5. Evaluate on Test Set
    X_test_lbp, test_crcs, y_test = extract_features_and_crcs(
        data_dir, 'test', face_detector, eye_detector, reflection_extractor, metrics_calculator
    )
    
    test_tex_scores = texture_clf.predict_proba(X_test_lbp)[:, 1]
    test_combined = best_w_tex * test_tex_scores + best_w_crcs * (test_crcs / 100.0)
    test_preds = (test_combined >= 0.5).astype(int)
    
    acc = accuracy_score(y_test, test_preds)
    prec = precision_score(y_test, test_preds)
    rec = recall_score(y_test, test_preds)
    f1 = f1_score(y_test, test_preds)
    
    # Print metrics
    print("\n" + "="*50)
    print("      OPTIMIZED WEIGHTED FUSION TEST METRICS")
    print("="*50)
    print(f"Accuracy  : {acc:.4%}")
    print(f"Precision : {prec:.4%}")
    print(f"Recall    : {rec:.4%}")
    print(f"F1-Score  : {f1:.4%}")
    print("="*50)
    
    # Save performance evaluation report
    report_path = 'outputs/fusion_v3/test_evaluation.json'
    evaluation_stats = {
        'accuracy': acc,
        'precision': prec,
        'recall': rec,
        'f1_score': f1,
        'optimal_weights': {
            'w_tex': best_w_tex,
            'w_crcs': best_w_crcs
        }
    }
    with open(report_path, 'w') as f:
        json.dump(evaluation_stats, f, indent=4)
    print(f"Saved test metrics report to {report_path}")

if __name__ == "__main__":
    main()
