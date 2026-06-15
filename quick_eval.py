import os
import glob
from main import Detection

class MockArgs:
    def __init__(self, img_path):
        self.input = img_path
        self.output = "dummy"
        self.radius_min_para = 4.5
        self.radius_max_para = 2.0
        self.shrink = True
        self.shrink_size = 2
        self.threshold_scale_left = 1.2
        self.threshold_scale_right = 1.2
        self.predictor_path = './shape_predictor/shape_predictor_68_face_landmarks.dat'
        self.threshold = 0.55
        self.headless = True
        
        # Disable V3 Models for quick texture validation on variance fallback
        self.texture_model = None
        self.fusion_clf = None
        self.efficientnet_model = None

fake_dir = "dataset_split/val/fake"
# Get first 30 fake images
fake_imgs = glob.glob(os.path.join(fake_dir, "*.jpg"))[:30]

print("--- Testing FAKE Images for Texture Score [0.0 - 0.6] ---")
for img in fake_imgs:
    args = MockArgs(img)
    try:
        res = Detection(args)
        if res:
             print(f"[FAKE] {os.path.basename(img)} - Texture Score: {res['texture']:.4f}, Variance: {res['variance']:.2f}")
    except Exception as e:
        print(f"Error on {img}: {e}")
