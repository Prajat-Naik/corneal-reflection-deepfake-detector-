import os
import cv2
import numpy as np
import uuid

from backend.src.face_detection import FaceDetector
from backend.src.eye_detection import EyeDetector
from backend.src.reflection_extractor import SpecularReflectionExtractor
from backend.src.metrics_calculator import MetricsCalculator

class DeepfakePredictor:
    def __init__(self, output_dir=None):
        self.face_detector = FaceDetector()
        self.eye_detector = EyeDetector()
        self.reflection_extractor = SpecularReflectionExtractor()
        self.metrics_calculator = MetricsCalculator()
        
        # Configure output folder path
        if output_dir is None:
            self.output_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                'static', 'results'
            )
        else:
            self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        # ML Model Integration (V3)
        self.use_ml = False
        self.device = None
        model_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        cnn_path = os.path.join(model_dir, 'outputs', 'efficientnet', 'best_model.pth')
        fusion_path = os.path.join(model_dir, 'outputs', 'fusion_v3', 'fusion_model.pkl')
        
        if os.path.exists(cnn_path) and os.path.exists(fusion_path):
            try:
                import torch
                import torch.nn as nn
                from torchvision import models, transforms
                import joblib
                
                self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                
                # Reconstruct and load EfficientNet-B0
                self.cnn_model = models.efficientnet_b0(pretrained=False)
                num_ftrs = self.cnn_model.classifier[1].in_features
                self.cnn_model.classifier[1] = nn.Linear(num_ftrs, 1)
                
                checkpoint = torch.load(cnn_path, map_location=self.device)
                if isinstance(checkpoint, dict):
                    self.cnn_model.load_state_dict(checkpoint)
                else:
                    self.cnn_model = checkpoint
                self.cnn_model = self.cnn_model.to(self.device)
                self.cnn_model.eval()
                
                # Load Fusion Meta-Classifier
                self.fusion_clf = joblib.load(fusion_path)
                
                # Input transform for CNN
                self.transform = transforms.Compose([
                    transforms.Resize((224, 224)),
                    transforms.ToTensor(),
                    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
                ])
                
                self.use_ml = True
                print("[DeepfakePredictor] Successfully loaded V3 Fusion Model & CNN weights!")
            except Exception as e:
                print(f"[DeepfakePredictor] Warning: Failed to initialize V3 ML models: {e}")

    def analyze_image(self, image_path):
        """
        Analyzes a single portrait image and returns complete explainable metrics and annotated plots.
        """
        # Read image
        image = cv2.imread(image_path)
        if image is None:
            return False, {"error": "Image file could not be read or is corrupted."}

        filename_base = str(uuid.uuid4())

        # 1. Face Detection
        face_ok, face_res = self.face_detector.detect_face(image)
        if not face_ok:
            return False, {"error": face_res["error"]}

        face_crop = face_res["crop"]
        face_confidence = face_res["confidence"]
        face_coords = face_res["coords_str"]
        annotated_face = face_res["annotated_image"]

        # 2. Eye Localizer & Landmark Detection
        eye_ok, eye_res = self.eye_detector.detect_and_crop_eyes(image)
        if not eye_ok:
            return False, {"error": eye_res["error"]}

        l_img = eye_res["left_img"]
        r_img = eye_res["right_img"]
        l_mask = eye_res["left_mask"]
        r_mask = eye_res["right_mask"]
        annotated_mesh = eye_res["annotated_mesh"]

        # 3. Specular Highlight Blob Extraction
        l_refl_mask, l_blobs = self.reflection_extractor.extract_highlights(l_img, l_mask)
        r_refl_mask, r_blobs = self.reflection_extractor.extract_highlights(r_img, r_mask)

        # Retrieve primary blobs
        l_primary = l_blobs[0] if len(l_blobs) > 0 else None
        r_primary = r_blobs[0] if len(r_blobs) > 0 else None

        # 4. Metrics Calculations
        l_size = (l_img.shape[1], l_img.shape[0])
        r_size = (r_img.shape[1], r_img.shape[0])
        
        rsi, rsi_breakdown = self.metrics_calculator.calculate_rsi(l_primary, r_primary, l_size, r_size)
        crcs = self.metrics_calculator.calculate_crcs(
            rsi, rsi_breakdown["position"], rsi_breakdown["brightness"], rsi_breakdown["distance_mismatch"]
        )
        ssim = self.metrics_calculator.calculate_ssim(l_img, r_img, l_primary, r_primary)

        # 5. Trust Score & Verdict Formulation
        use_ml_success = False
        cnn_fake_prob = 0.5
        reflection_fake_prob = 0.5

        if self.use_ml:
            try:
                from PIL import Image
                import torch
                
                # A. CNN prediction (probability of FAKE)
                img_pil = Image.open(image_path).convert('RGB')
                img_t = self.transform(img_pil).unsqueeze(0).to(self.device)
                with torch.no_grad():
                    logits = self.cnn_model(img_t)
                    cnn_fake_prob = torch.sigmoid(logits).item()
                
                # B. Reflection Consistency prediction (0.0=Fake, 1.0=Real)
                from corneal_reflection import CornealReflectionAnalyzer
                analyzer = CornealReflectionAnalyzer()
                reflection_consistency = analyzer.calculate_consistency_score(image_path)
                reflection_fake_prob = 1.0 - reflection_consistency
                
                # C. Fusion Classifier prediction
                features = np.array([[cnn_fake_prob, reflection_fake_prob]])
                fusion_fake_prob = self.fusion_clf.predict_proba(features)[0][1]
                
                # Trust Score represents probability of being REAL (0 - 100)
                trust_score = int((1.0 - fusion_fake_prob) * 100)
                risk_level = self.metrics_calculator.interpret_trust_score(trust_score)
                result = "REAL" if trust_score >= 50 else "DEEPFAKE"
                confidence = float(100.0 - trust_score) if result == "DEEPFAKE" else float(trust_score)
                
                use_ml_success = True
            except Exception as e:
                print(f"[DeepfakePredictor] Error during ML prediction: {e}. Falling back to heuristic.")

        if not use_ml_success:
            # Trust Score Formula (Heuristic Fallback)
            trust_score = int((rsi * 0.3 + (crcs / 100.0) * 0.4 + ssim * 0.3) * 100)
            risk_level = self.metrics_calculator.interpret_trust_score(trust_score)
            result = "REAL" if trust_score >= 65 else "DEEPFAKE"
            if result == "REAL":
                confidence = max(65.0, min(99.0, float(trust_score)))
            else:
                confidence = max(65.0, min(99.0, 100.0 - float(trust_score)))

        # 6. Explainable AI Reasoning Reasons Checklist
        reasons = []
        if use_ml_success:
            # Highlight CNN skin texture finding
            if cnn_fake_prob > 0.5:
                reasons.append(f"Skin texture artifacts detected (CNN score: {cnn_fake_prob:.2f})")
            # Highlight corneal reflection consistency finding
            if reflection_fake_prob > 0.5:
                reasons.append(f"Inconsistent ocular reflection alignment (reflection score: {reflection_fake_prob:.2f})")
            
            # If the final verdict is DEEPFAKE but individual scores didn't exceed 0.5 alone
            if result == "DEEPFAKE" and not reasons:
                reasons.append("Combined biometric and texture analysis flagged anomalies")
        else:
            # Position Mismatch Check: Mismatch distance > 0.08 is suspicious
            pos_mismatch = rsi_breakdown["distance_mismatch"] > 0.08
            if pos_mismatch:
                reasons.append("Reflection Position Mismatch detected")
            
            # Brightness Difference Check
            bright_diff = abs((l_primary["brightness"] if l_primary else 0) - (r_primary["brightness"] if r_primary else 0)) > 25
            if bright_diff:
                reasons.append("Reflection Brightness Difference detected")
    
            # Low RSI Check
            if rsi < 0.70:
                reasons.append("Low Reflection Symmetry Index (RSI)")
            
            # Low SSIM Check
            if ssim < 0.75:
                reasons.append("Low Structural Similarity Score (SSIM)")

        explanation = "; ".join(reasons) if reasons else "Ocular highlights reflect environments symmetrically."

        # 7. Generate Visual Output Artifacts for Display
        face_path = f"{filename_base}_face.png"
        mesh_path = f"{filename_base}_mesh.png"
        l_crop_path = f"{filename_base}_l_crop.png"
        r_crop_path = f"{filename_base}_r_crop.png"
        l_refl_path = f"{filename_base}_l_refl.png"
        r_refl_path = f"{filename_base}_r_refl.png"
        comparison_path = f"{filename_base}_comparison.png"

        # Save images
        cv2.imwrite(os.path.join(self.output_dir, face_path), annotated_face)
        cv2.imwrite(os.path.join(self.output_dir, mesh_path), annotated_mesh)
        cv2.imwrite(os.path.join(self.output_dir, l_crop_path), l_img)
        cv2.imwrite(os.path.join(self.output_dir, r_crop_path), r_img)
        
        # Binary reflection highlights
        cv2.imwrite(os.path.join(self.output_dir, l_refl_path), l_refl_mask)
        cv2.imwrite(os.path.join(self.output_dir, r_refl_path), r_refl_mask)

        # Draw contour highlights side by side
        l_draw = l_img.copy()
        r_draw = r_img.copy()
        if l_primary:
            cv2.drawContours(l_draw, [l_primary["contour"]], -1, (0, 255, 0), 1)
        if r_primary:
            cv2.drawContours(r_draw, [r_primary["contour"]], -1, (0, 0, 255), 1)

        # Pad to equal heights
        max_h = max(l_draw.shape[0], r_draw.shape[0])
        def pad_h(img, th):
            h, w = img.shape[:2]
            if h < th:
                return cv2.copyMakeBorder(img, 0, th - h, 0, 0, cv2.BORDER_CONSTANT, value=0)
            return img
        
        comparison_img = np.hstack((pad_h(l_draw, max_h), pad_h(r_draw, max_h)))
        cv2.imwrite(os.path.join(self.output_dir, comparison_path), comparison_img)

        # Return comprehensive metrics pack
        return True, {
            "media_name": os.path.basename(image_path),
            "result": result,
            "confidence": confidence,
            "trust_score": trust_score,
            "risk_level": risk_level,
            "rsi": rsi,
            "crcs": crcs,
            "ssim": ssim,
            "explanation": explanation,
            "face_confidence": face_confidence,
            "face_coords": face_coords,
            "reasons": reasons,
            "visuals": {
                "face_url": f"/static/results/{face_path}",
                "mesh_url": f"/static/results/{mesh_path}",
                "l_crop_url": f"/static/results/{l_crop_path}",
                "r_crop_url": f"/static/results/{r_crop_path}",
                "l_refl_url": f"/static/results/{l_refl_path}",
                "r_refl_url": f"/static/results/{r_refl_path}",
                "comparison_url": f"/static/results/{comparison_path}"
            },
            "blobs_details": {
                "left": {
                    "position": [round(x, 2) for x in l_primary["position"]] if l_primary else [0.0, 0.0],
                    "area": float(l_primary["area"]) if l_primary else 0.0,
                    "brightness": float(l_primary["brightness"]) if l_primary else 0.0
                },
                "right": {
                    "position": [round(x, 2) for x in r_primary["position"]] if r_primary else [0.0, 0.0],
                    "area": float(r_primary["area"]) if r_primary else 0.0,
                    "brightness": float(r_primary["brightness"]) if r_primary else 0.0
                }
            }
        }
