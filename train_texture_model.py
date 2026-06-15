
import os
import cv2
import numpy as np
import joblib
import argparse
from skimage import feature
from sklearn.svm import SVC, LinearSVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def compute_lbp_feature(image, radius=3, n_points=24):
    """
    Compute Local Binary Pattern (LBP) histogram for texture classification.
    """
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # Uniform LBP is rotation invariant and robust
    lbp = feature.local_binary_pattern(gray, n_points, radius, method="uniform")
    
    # Calculate histogram
    # n_points + 2 is the number of bins for 'uniform' method
    (hist, _) = np.histogram(lbp.ravel(), bins=np.arange(0, n_points + 3), range=(0, n_points + 2))

    # Normalize the histogram
    hist = hist.astype("float")
    hist /= (hist.sum() + 1e-7)

    return hist

def get_image_paths(directory):
    # Recursively find all images
    valid_exts = {'.png', '.jpg', '.jpeg'}
    image_paths = []
    for root, _, files in os.walk(directory):
        for file in files:
            if os.path.splitext(file)[1].lower() in valid_exts:
                image_paths.append(os.path.join(root, file))
    return image_paths

def load_data(real_dir, fake_dir, max_images=None):
    """
    Load images and extract LBP features.
    """
    data = []
    labels = []
    
    # Real = 1, Fake = 0 (Matches our scoring logic: High score = Real)
    
    real_files = get_image_paths(real_dir)
    logger.info(f"Found {len(real_files)} Real images in {real_dir}")
    
    if max_images: real_files = real_files[:max_images]
    
    for file in real_files:
        try:
            img = cv2.imread(file)
            if img is not None:
                 # Resize to standard size to ensure consistent texture scale? 
                 # LBP is somewhat scale dependent. Let's resize face to 512x512 if larger, or keep as is.
                 # standard resizing is safer.
                 h, w = img.shape[:2]
                 # Only resize if small? No, force consistent scale.
                 img = cv2.resize(img, (512, 512))
                 hist = compute_lbp_feature(img)
                 data.append(hist)
                 labels.append(1) # REAL
        except Exception as e:
            logger.warning(f"Failed to process {file}: {e}")

    fake_files = get_image_paths(fake_dir)
    logger.info(f"Found {len(fake_files)} Fake images in {fake_dir}")

    if max_images: fake_files = fake_files[:max_images]
    
    for file in fake_files:
        try:
            img = cv2.imread(file)
            if img is not None:
                 img = cv2.resize(img, (512, 512))
                 hist = compute_lbp_feature(img)
                 data.append(hist)
                 labels.append(0) # FAKE
        except Exception as e:
            logger.warning(f"Failed to process {file}: {e}")

    return np.array(data), np.array(labels)

def load_data_from_split(base_dir, max_images=None):
    """
    Load data from a directory containing 'real' and 'fake' subdirectories.
    """
    real_dir = os.path.join(base_dir, 'real')
    fake_dir = os.path.join(base_dir, 'fake')
    
    data = []
    labels = []
    
    # Load Real
    if os.path.exists(real_dir):
        real_files = get_image_paths(real_dir)
        logger.info(f"Found {len(real_files)} Real images in {real_dir}")
        if max_images: real_files = real_files[:max_images]
        for file in real_files:
            try:
                img = cv2.imread(file)
                if img is not None:
                     img = cv2.resize(img, (512, 512))
                     hist = compute_lbp_feature(img)
                     data.append(hist)
                     labels.append(1)
            except: pass
            
    # Load Fake
    if os.path.exists(fake_dir):
        fake_files = get_image_paths(fake_dir)
        logger.info(f"Found {len(fake_files)} Fake images in {fake_dir}")
        if max_images: fake_files = fake_files[:max_images]
        for file in fake_files:
            try:
                img = cv2.imread(file)
                if img is not None:
                     img = cv2.resize(img, (512, 512))
                     hist = compute_lbp_feature(img)
                     data.append(hist)
                     labels.append(0)
            except: pass
            
    return np.array(data), np.array(labels)

def train_model(real_dir=None, fake_dir=None, train_dir=None, test_dir=None, output_model="texture_model.pkl"):
    
    # 1. Load Training Data
    if train_dir:
        logger.info(f"Loading Training Data from {train_dir}...")
        trainData, trainLabels = load_data_from_split(train_dir)
    elif real_dir and fake_dir:
        logger.info(f"Loading Data from {real_dir} and {fake_dir}...")
        data, labels = load_data(real_dir, fake_dir)
        # Split internally if no explicit test set provided later
        if not test_dir:
             (trainData, testData, trainLabels, testLabels) = train_test_split(data, labels, test_size=0.20, random_state=42)
        else:
             trainData, trainLabels = data, labels
    else:
        logger.error("Must provide either --train_dir OR --real/--fake directories.")
        return

    # 2. Load Test Data (Optional)
    if test_dir:
        logger.info(f"Loading Test Data from {test_dir}...")
        testData, testLabels = load_data_from_split(test_dir)
    elif not train_dir and not test_dir:
        # Already split above
        pass
    else:
        testData, testLabels = None, None

    if len(trainData) == 0:
        logger.error("No training data found.")
        return

    logger.info(f"Training with {len(trainData)} samples...")
    model = SVC(kernel="rbf", C=1.0, gamma='scale', probability=True, random_state=42)
    model.fit(trainData, trainLabels)

    # 3. Evaluate
    if testData is not None and len(testData) > 0:
        logger.info("Evaluating model on Test Set...")
        predictions = model.predict(testData)
        acc = accuracy_score(testLabels, predictions)
        logger.info(f"Test Accuracy: {acc:.2%}")
        print(classification_report(testLabels, predictions, target_names=["Fake", "Real"]))
    else:
        logger.info("No test data provided. Skipping evaluation.")

    logger.info(f"Saving model to {output_model}...")
    joblib.dump(model, output_model)
    logger.info("Done.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--real", default=None, help="Path to real images (Legacy mode)")
    parser.add_argument("--fake", default=None, help="Path to fake images (Legacy mode)")
    parser.add_argument("--train_dir", default=None, help="Path to training directory (contains real/fake)")
    parser.add_argument("--test_dir", default=None, help="Path to test directory (contains real/fake)")
    parser.add_argument("--out", default="texture_model.pkl", help="Output model file")
    args = parser.parse_args()
    
    # Fallback for legacy behavior if no args provided
    if not args.train_dir and not args.real:
        if os.path.exists("dataset/real") and os.path.exists("dataset/fake"):
             args.real = "dataset/real"
             args.fake = "dataset/fake"
    
    train_model(real_dir=args.real, fake_dir=args.fake, train_dir=args.train_dir, test_dir=args.test_dir, output_model=args.out)
