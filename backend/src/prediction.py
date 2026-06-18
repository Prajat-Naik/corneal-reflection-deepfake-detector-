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
        self.texture_model = None
        model_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        texture_model_path = os.path.join(model_dir, 'texture_model.pkl')
        
        if os.path.exists(texture_model_path):
            try:
                import joblib
                self.texture_model = joblib.load(texture_model_path)
                print("[DeepfakePredictor] Successfully loaded face texture SVM model!")
            except Exception as e:
                print(f"[DeepfakePredictor] Warning: Failed to load texture SVM: {e}")

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

        # 5. Face Texture Score Calculation
        from crop_highlights import analyze_face_texture
        texture_score, texture_variance = analyze_face_texture(face_crop, model=self.texture_model)

        # 6. Combined Prediction Score (Weighted Fusion)
        # Load optimized weights dynamically
        model_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        weights_path = os.path.join(model_dir, 'outputs', 'fusion_v3', 'fusion_weights.json')
        w_tex, w_crcs = 0.6, 0.4
        if os.path.exists(weights_path):
            try:
                import json
                with open(weights_path, 'r') as f:
                    w_data = json.load(f)
                    w_tex = w_data.get('w_tex', 0.6)
                    w_crcs = w_data.get('w_crcs', 0.4)
            except Exception:
                pass

        final_score = w_tex * texture_score + w_crcs * (crcs / 100.0)
        trust_score = int(final_score * 100)
        risk_level = self.metrics_calculator.interpret_trust_score(trust_score)
        
        result = "REAL" if trust_score >= 50 else "DEEPFAKE"
        confidence = float(trust_score) if result == "REAL" else float(100.0 - trust_score)

        # 7. Explainable AI Reasoning Checklist
        reasons = []
        if texture_score < 0.5:
            reasons.append(f"Irregular facial micro-texture detected (authenticity score: {texture_score:.2f})")
        if (crcs / 100.0) < 0.5:
            reasons.append(f"Inconsistent ocular corneal reflection alignment (CRCS score: {crcs:.1f} / 100)")
            
        if result == "DEEPFAKE" and not reasons:
            reasons.append("Combined biometric and texture analysis flagged anomalies")

        explanation = "; ".join(reasons) if reasons else "Ocular highlights reflect environments symmetrically with authentic facial micro-textures."

        # 8. Generate Visual Output Artifacts for Display
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
            "texture_score": texture_score,
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
