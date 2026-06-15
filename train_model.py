import os
import cv2
import numpy as np
import joblib
import argparse
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import matplotlib.pyplot as plt

# Custom self-contained Feature Extractor using skimage
from skimage import feature

class FeatureExtractor:
    def compute_lbp_histogram(self, image, radius=3, n_points=24):
        """
        Compute Local Binary Pattern (LBP) histogram for texture classification.
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Uniform LBP is rotation invariant and robust
        try:
            lbp = feature.local_binary_pattern(gray, n_points, radius, method="uniform")
            
            # Calculate histogram
            (hist, _) = np.histogram(lbp.ravel(), bins=np.arange(0, n_points + 3), range=(0, n_points + 2))

            # Normalize the histogram
            hist = hist.astype("float")
            hist /= (hist.sum() + 1e-7)
            return hist
        except Exception as e:
            print(f"LBP Error: {e}")
            return np.zeros(n_points + 2)


def extract_dataset_features(real_dir, fake_dir, max_images=None):
    """
    Scans real and fake directories, crops faces, and extracts LBP micro-texture features.
    """
    extractor = FeatureExtractor()
    features = []
    labels = []

    print("[Training Node] Initializing feature extraction...")
    
    # 1. Process REAL images (Class 1)
    if os.path.exists(real_dir):
        real_files = [os.path.join(real_dir, f) for f in os.listdir(real_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        print(f"[Training Node] Located {len(real_files)} REAL images.")
        if max_images: real_files = real_files[:max_images]
        
        for file in real_files:
            try:
                img = cv2.imread(file)
                if img is not None:
                    # Resize to force consistent scale
                    img_resized = cv2.resize(img, (512, 512))
                    hist = extractor.compute_lbp_histogram(img_resized)
                    features.append(hist)
                    labels.append(1) # Class 1 = REAL
            except Exception as e:
                print(f"[Training Node] Skipped REAL file {file}: {e}")

    # 2. Process FAKE images (Class 0)
    if os.path.exists(fake_dir):
        fake_files = [os.path.join(fake_dir, f) for f in os.listdir(fake_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        print(f"[Training Node] Located {len(fake_files)} FAKE images.")
        if max_images: fake_files = fake_files[:max_images]
        
        for file in fake_files:
            try:
                img = cv2.imread(file)
                if img is not None:
                    img_resized = cv2.resize(img, (512, 512))
                    hist = extractor.compute_lbp_histogram(img_resized)
                    features.append(hist)
                    labels.append(0) # Class 0 = FAKE
            except Exception as e:
                print(f"[Training Node] Skipped FAKE file {file}: {e}")

    return np.array(features), np.array(labels)

def generate_performance_plots(y_true, y_pred, output_dir):
    """
    Generates academic evaluation charts and confusion matrix plots using plain matplotlib.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Confusion Matrix Custom Heatmap
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)
    
    ax.set(xticks=np.arange(cm.shape[1]),
           yticks=np.arange(cm.shape[0]),
           xticklabels=['Fake', 'Real'], 
           yticklabels=['Fake', 'Real'],
           title='AuraEye Confusion Matrix',
           ylabel='Actual Label',
           xlabel='Predicted Label')
    
    # Annotate inside blocks
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], 'd'),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black",
                    fontweight='bold')
            
    fig.tight_layout()
    cm_path = os.path.join(output_dir, 'confusion_matrix.png')
    plt.savefig(cm_path, dpi=300)
    plt.close()
    print(f"[Evaluation] Saved Confusion Matrix to: {cm_path}")

    # 2. Performance Metrics Bar Chart
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred)
    rec = recall_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)
    
    metrics = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
    values = [acc, prec, rec, f1]
    colors = ['#6366f1', '#a855f7', '#06b6d4', '#10b981'] # Cyber gradients palette
    
    plt.figure(figsize=(6, 4.5))
    bars = plt.bar(metrics, values, color=colors, width=0.55, edgecolor=(1, 1, 1, 0.1), linewidth=1)
    plt.title('AuraEye Forensic Classifier Performance', fontsize=12, fontweight='bold', pad=15)
    plt.ylim(0, 1.1)
    
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, height + 0.02, f"{height:.2%}", 
                 ha='center', va='bottom', fontweight='bold', fontsize=9)
                 
    plt.ylabel('Score Value', fontsize=10)
    plt.grid(axis='y', linestyle='--', alpha=0.15)
    plt.tight_layout()
    chart_path = os.path.join(output_dir, 'performance_metrics.png')
    plt.savefig(chart_path, dpi=300)
    plt.close()
    print(f"[Evaluation] Saved Performance Comparison Chart to: {chart_path}")


def main():
    parser = argparse.ArgumentParser(description="AuraEye SVM Texture Classifier Trainer")
    parser.add_argument('--dataset', default='dataset', help='Path to dataset directory containing real/fake sub-folders')
    parser.add_argument('--out', default='texture_model.pkl', help='Output path for saved SVM classifier weight')
    parser.add_argument('--plots', default='static/results', help='Directory to export metric graphics')
    args = parser.parse_args()

    real_dir = os.path.join(args.dataset, 'real')
    fake_dir = os.path.join(args.dataset, 'fake')

    if not os.path.exists(real_dir) or not os.path.exists(fake_dir):
        print(f"[Error] Dataset directory structure not found. Ensure '{real_dir}' and '{fake_dir}' exist.")
        return

    # Extract biometric features
    X, y = extract_dataset_features(real_dir, fake_dir)
    
    if len(X) == 0:
        print("[Error] No training features extracted. Check images inside dataset directory.")
        return

    # Train / Test split (80/20 Split)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)
    print(f"[Training Node] Training Set Size: {len(X_train)} | Validation Set Size: {len(X_test)}")

    # Initialize Scikit-Learn SVM with RBF kernel and probability configurations
    print("[Training Node] Fitting Support Vector Machine (RBF Kernel)...")
    clf = SVC(kernel='rbf', C=1.0, gamma='scale', probability=True, random_state=42)
    clf.fit(X_train, y_train)

    # Evaluate
    y_pred = clf.predict(X_test)
    
    print("\n" + "="*50)
    print("           AURAEYE FORENSICS CLASSIFIER EVALUATION")
    print("="*50)
    print(f"Accuracy  : {accuracy_score(y_test, y_pred):.4%}")
    print(f"Precision : {precision_score(y_test, y_pred):.4%}")
    print(f"Recall    : {recall_score(y_test, y_pred):.4%}")
    print(f"F1-Score  : {f1_score(y_test, y_pred):.4%}")
    print("-"*50)
    print("\nDetailed Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Fake', 'Real']))
    print("="*50)

    # Generate academic performance plots
    generate_performance_plots(y_test, y_pred, args.plots)

    # Save trained model weights
    os.makedirs('model', exist_ok=True)
    model_output_paths = [args.out, os.path.join('model', 'svm_model.pkl')]
    
    for path in model_output_paths:
        print(f"[Training Node] Saving classifier to: {path}")
        joblib.dump(clf, path)

    print("[Training Node] Model training execution completed successfully!")

if __name__ == "__main__":
    main()
