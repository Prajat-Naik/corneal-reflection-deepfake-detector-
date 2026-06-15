# Deepfake Detection V2: EfficientNet + Corneal Reflection Fusion

This is an advanced deepfake detection pipeline that combines Deep Learning (EfficientNet-B0) with Physics-based analysis (Corneal Reflection Consistency).

## Components

1.  **`train_efficientnet.py`**:
    - Trains an EfficientNet-B0 model on your dataset.
    - Uses MediaPipe to crop faces automatically.
    - Applies heavy augmentations (Flip, Rotate, Color Jitter).
    - Saves the best model to `outputs/efficientnet/best_model.pth`.

2.  **`corneal_reflection.py`**:
    - A module that analyzes eye reflections.
    - Calculates a consistency score based on **SSIM** (Structure) and **Brightness**.
    - Real eyes have high consistency; GANs often fail here.

3.  **`fusion_inference.py`**:
    - Combines the CNN probability and Reflection Score.
    - Formula: `Final Score = 0.7 * CNN + 0.3 * Reflection`
    - Generates `fusion_predictions.csv` and confusion matrices.

## How to Run

### 1. Install Dependencies
```bash
pip install torch torchvision tqdm scikit-image mediapipe sklearn matplotlib pandas
```

### 2. Train the Deep Learning Model
**Note:** This takes time. A GPU is highly recommended.
```bash
python train_efficientnet.py --data_dir dataset_split --epochs 20
```
*Output: `outputs/efficientnet/best_model.pth`*

### 3. Run Fusion Evaluation
Once training is done, evaluate on the Test set:
```bash
python fusion_inference.py --test_dir dataset_split/test --model_path outputs/efficientnet/best_model.pth
```
*Output: `outputs/fusion/fusion_predictions.csv`, `metrics.txt`, `confusion_matrix.png`*
