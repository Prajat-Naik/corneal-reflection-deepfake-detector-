import cv2
import mediapipe as mp
import numpy as np
from skimage.metrics import structural_similarity as ssim

class CornealReflectionAnalyzer:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )
        # Iris indices (Refined landmarks)
        self.LEFT_IRIS = [474, 475, 476, 477]
        self.RIGHT_IRIS = [469, 470, 471, 472]

    def crop_eye_region(self, image, landmarks, iris_indices, pad=10):
        h, w, _ = image.shape
        x_min, x_max = w, 0
        y_min, y_max = h, 0
        
        for idx in iris_indices:
            pt = landmarks[idx]
            x, y = int(pt.x * w), int(pt.y * h)
            x_min, x_max = min(x_min, x), max(x_max, x)
            y_min, y_max = min(y_min, y), max(y_max, y)
            
        # Add padding
        x_min = max(0, x_min - pad)
        y_min = max(0, y_min - pad)
        x_max = min(w, x_max + pad)
        y_max = min(h, y_max + pad)
        
        return image[y_min:y_max, x_min:x_max]

    def extract_highlights(self, eye_img):
        """Robust highlight isolation using adaptive CLAHE and percentile limit-gating"""
        if eye_img.size == 0: return None
        gray = cv2.cvtColor(eye_img, cv2.COLOR_BGR2GRAY)
        # Apply CLAHE to enhance local contrast of true highlights
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Enforce an absolute intensity floor of 180 alongside the top 5% percentile
        # This keeps us from selecting dark iris/skin pixels as false positive highlights in low light
        thresh_percentile = np.percentile(enhanced, 95)
        thresh_val = max(180.0, thresh_percentile)
        
        _, mask = cv2.threshold(enhanced, thresh_val, 255, cv2.THRESH_BINARY)
        
        # Keep only large enough highlights to filter out high-frequency noise
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        clean_mask = np.zeros_like(mask)
        
        for cnt in contours:
            if cv2.contourArea(cnt) > 2: # Min pixel size
                cv2.drawContours(clean_mask, [cnt], -1, 255, -1)
                
        return clean_mask

    def check_anisocoria(self, left_eye, right_eye):
        """
        Anisocoria Test: Estimates pupil diameter symmetry by thresholding the darkest pixels
        representing the pupil and verifying if the sizes match biological constraints.
        """
        try:
            gray_l = cv2.cvtColor(left_eye, cv2.COLOR_BGR2GRAY)
            gray_r = cv2.cvtColor(right_eye, cv2.COLOR_BGR2GRAY)
            
            # Pupils are the darkest segment (bottom 15% brightness)
            th_l = min(np.percentile(gray_l, 15), 80.0)
            th_r = min(np.percentile(gray_r, 15), 80.0)
            
            pupil_l = np.sum(gray_l < th_l)
            pupil_r = np.sum(gray_r < th_r)
            
            if pupil_l == 0 or pupil_r == 0:
                return 1.0 # Default to pass if cannot estimate
                
            ratio = min(pupil_l, pupil_r) / max(pupil_l, pupil_r)
            return ratio
        except Exception:
            return 1.0

    def check_iris_color(self, left_eye, right_eye):
        """
        Iris Color Matching: Computes a 3D HSV color histogram of both eye regions
        to verify that both eyes belong to the same individual.
        """
        try:
            hsv_l = cv2.cvtColor(left_eye, cv2.COLOR_BGR2HSV)
            hsv_r = cv2.cvtColor(right_eye, cv2.COLOR_BGR2HSV)
            
            # Compute 3D HSV histogram (8 bins per channel)
            hist_l = cv2.calcHist([hsv_l], [0, 1, 2], None, [8, 8, 8], [0, 180, 0, 256, 0, 256])
            hist_r = cv2.calcHist([hsv_r], [0, 1, 2], None, [8, 8, 8], [0, 180, 0, 256, 0, 256])
            
            cv2.normalize(hist_l, hist_l)
            cv2.normalize(hist_r, hist_r)
            
            similarity = cv2.compareHist(hist_l, hist_r, cv2.HISTCMP_CORREL)
            return max(0.0, similarity)
        except Exception:
            return 1.0

    def calculate_consistency_score(self, image_path):
        """
        Returns a consistency score (0.0 to 1.0) combining optical and biological symmetry.
        Higher score = More consistent (likely Real).
        Lower score = Inconsistent (likely Fake).
        """
        img = cv2.imread(image_path)
        if img is None: return 0.5
        
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(img_rgb)
        
        if not results.multi_face_landmarks:
            return 0.5 # Neutral if no face
            
        landmarks = results.multi_face_landmarks[0].landmark
        
        # Crop Eyes
        left_eye = self.crop_eye_region(img, landmarks, self.LEFT_IRIS)
        right_eye = self.crop_eye_region(img, landmarks, self.RIGHT_IRIS)
        
        if left_eye.size == 0 or right_eye.size == 0:
            return 0.5
        
        # Get Highlights
        left_high = self.extract_highlights(left_eye)
        right_high = self.extract_highlights(right_eye)
        
        if left_high is None or right_high is None:
            return 0.5
            
        # Resize right to match left for comparison
        right_high_resized = cv2.resize(right_high, (left_high.shape[1], left_high.shape[0]))
        
        # Score 1: Specular highlight SSIM (Structural Similarity)
        # Flip right eye reflection horizontally to account for mirroring geometry
        right_high_flipped = cv2.flip(right_high_resized, 1)
        score_ssim = ssim(left_high, right_high_flipped)
        
        # Score 2: Average Brightness Consistency
        mean_l = np.mean(left_eye)
        mean_r = np.mean(right_eye)
        score_bright = 1.0 - (abs(mean_l - mean_r) / 255.0)
        
        # Score 3: Anisocoria Check (Pupil sizes symmetry)
        score_anisocoria = self.check_anisocoria(left_eye, right_eye)
        
        # Score 4: Iris Color Matching (Pigmentation histogram)
        score_color = self.check_iris_color(left_eye, right_eye)
        
        # Final weighted physical score
        final_score = (0.5 * score_ssim) + (0.2 * score_bright) + (0.15 * score_anisocoria) + (0.15 * score_color)
        final_score = max(0.0, min(1.0, final_score))
        
        return final_score

if __name__ == "__main__":
    # Test
    analyzer = CornealReflectionAnalyzer()
    # Placeholder test
    print("Corneal Reflection Analyzer Initialized.")
