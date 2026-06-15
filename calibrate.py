
import os
import argparse
import numpy as np
from main import Detection

class Args:
    def __init__(self, input_path):
        self.input = input_path
        self.output = "dummy_output" # Not used but required
        self.radius_min_para = 4.5
        self.radius_max_para = 2.0
        self.shrink = True
        self.shrink_size = 2
        self.threshold_scale_left = 1.2
        self.threshold_scale_right = 1.2
        self.predictor_path = './shape_predictor/shape_predictor_68_face_landmarks.dat'
        self.threshold = 0.55 # Default, doesnt affect score calculation
        self.headless = True # Don't show plots

def process_folder(folder_path, label):
    """
    Process images in a folder and return a list of result dictionaries.
    Each dict contains: {'score', 'iou', 'texture', 'ssim'}
    """
    results = []
    print(f"\n--- Processing {label} Images in {folder_path} ---")
    
    if not os.path.exists(folder_path):
        print(f"Folder not found: {folder_path}")
        return []

    files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not files:
        print(f"No images found in {folder_path}")
        return []

    for filename in files:
        filepath = os.path.join(folder_path, filename)
        args = Args(filepath)
        try:
            # Detection returns a dict {'score', 'iou', 'texture', 'ssim'} or False
            metrics = Detection(args)
            
            if metrics is False:
                print(f"[FAIL] {filename}: Face/Eye not detected")
            else:
                results.append(metrics)
                # Print concise one-liner
                print(f"[OK] {filename}: Score={metrics['score']:.4f}, IOU={metrics['iou']:.4f}, Tex={metrics['texture']:.4f}, SSIM={metrics['ssim']:.4f}")
                
        except Exception as e:
            print(f"[ERR]  {filename}: {e}")

    return results

def print_stats(results, label):
    if not results:
        return
    
    count = len(results)
    
    # Extract lists
    scores = [r['score'] for r in results]
    ious = [r['iou'] for r in results]
    textures = [r['texture'] for r in results]
    ssims = [r['ssim'] for r in results]

    print(f"\n{label} Images Stats ({count} images):")
    print(f"  Final Score : Avg={np.mean(scores):.4f}, Min={np.min(scores):.4f}, Max={np.max(scores):.4f}")
    print(f"  IOU Score   : Avg={np.mean(ious):.4f}")
    print(f"  Texture     : Avg={np.mean(textures):.4f}")
    print(f"  SSIM        : Avg={np.mean(ssims):.4f}")

    return scores

def main():
    base_folder = "dataset_split"
    splits = ["train", "val", "test"]
    
    print("=== Deepfake Detection Calibration & Metrics (Dataset Split) ===\n")

    real_results = []
    fake_results = []
    
    for split in splits:
        real_folder = os.path.join(base_folder, split, "real")
        fake_folder = os.path.join(base_folder, split, "fake")
        
        fake_results.extend(process_folder(fake_folder, f"FAKE ({split})"))
        real_results.extend(process_folder(real_folder, f"REAL ({split})"))

    print("\n=== DETAILED METRICS (ALL SPLITS) ===")
    real_scores = print_stats(real_results, "REAL (Total)")
    fake_scores = print_stats(fake_results, "FAKE (Total)")

    # Accuracy Calculation
    # Suggested threshold logic remains, but we also calculate accuracy for current default (0.55)
    default_threshold = 0.55
    
    tp = 0 # Real classified as Real (Score >= Threshold)
    tn = 0 # Fake classified as Fake (Score < Threshold)
    fp = 0 # Fake classified as Real
    fn = 0 # Real classified as Fake
    
    if real_results:
        for r in real_results:
            # Re-calculate final score based on new logic (just in case main.py returned old score)
            # Actually main.py returns the *correct* final score in r['score'], 
            # so we can just use that directly.
            if r['score'] >= default_threshold:
                tp += 1
            else:
                fn += 1
                
    if fake_results:
        for r in fake_results:
            # Fake should be < threshold
            if r['score'] < default_threshold:
                tn += 1
            else:
                fp += 1
                
    total_samples = (len(real_results) if real_results else 0) + (len(fake_results) if fake_results else 0)
    
    if total_samples > 0:
        accuracy = (tp + tn) / total_samples
        print(f"\n=== ACCURACY (Threshold {default_threshold}) ===")
        print(f"  Accuracy: {accuracy:.2%} ({tp+tn}/{total_samples})")
        print(f"  True Positives  (Real->Real): {tp}")
        print(f"  True Negatives  (Fake->Fake): {tn}")
        print(f"  False Positives (Fake->Real): {fp}")
        print(f"  False Negatives (Real->Fake): {fn}")
    else:
        print("\nNo samples to calculate accuracy.")

    print("\n=== RECOMMENDATION ===")
    
    min_real = np.min(real_scores) if real_scores else None
    max_fake = np.max(fake_scores) if fake_scores else None
    
    if min_real is not None:
        # Suggested threshold: slightly below the minimum real score
        suggested = max(0.1, min_real - 0.05) 
        print(f"Based on your REAL images (Min Score: {min_real:.4f}), suggested threshold: {suggested:.2f}")
        
        if max_fake is not None and max_fake > suggested:
             print(f"WARNING: Overlap detected. Max Fake Score ({max_fake:.4f}) > Suggested Threshold.")
    else:
        print("Cannot suggest threshold without valid Real images.")

if __name__ == "__main__":
    main()
