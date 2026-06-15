import cv2
import numpy as np
from skimage.metrics import structural_similarity as compare_ssim

class MetricsCalculator:
    def calculate_rsi(self, l_blob, r_blob, l_size, r_size):
        """
        Calculates the Reflection Symmetry Index (RSI).
        
        Args:
            l_blob: Primary blob dict for the left eye (position, area, brightness) or None.
            r_blob: Primary blob dict for the right eye or None.
            l_size: (width, height) of left eye crop.
            r_size: (width, height) of right eye crop.
        Returns:
            rsi (float): 0.0 - 1.0
            similarities (dict): Breakdown of position, area, and brightness similarities.
        """
        if l_blob is None or r_blob is None:
            return 0.0, {"position": 0.0, "area": 0.0, "brightness": 0.0}

        # 1. Position Similarity (normalize centroids by crop dimensions)
        lx_rel = l_blob["position"][0] / l_size[0]
        ly_rel = l_blob["position"][1] / l_size[1]
        rx_rel = r_blob["position"][0] / r_size[0]
        ry_rel = r_blob["position"][1] / r_size[1]

        # Calculate coordinate distance mismatch
        dist = np.sqrt((lx_rel - rx_rel) ** 2 + (ly_rel - ry_rel) ** 2)
        # Scale: max mismatch expected relative to eye boundary is ~0.5
        pos_sim = max(0.0, 1.0 - (dist / 0.4))

        # 2. Area Similarity
        la = l_blob["area"]
        ra = r_blob["area"]
        if la == 0 or ra == 0:
            area_sim = 0.0
        else:
            area_sim = min(la, ra) / max(la, ra)

        # 3. Brightness Similarity
        lb = l_blob["brightness"]
        rb = r_blob["brightness"]
        if lb == 0 or rb == 0:
            bright_sim = 0.0
        else:
            bright_sim = min(lb, rb) / max(lb, rb)

        # Combine into average RSI
        rsi = (pos_sim + area_sim + bright_sim) / 3.0

        return rsi, {
            "position": pos_sim,
            "area": area_sim,
            "brightness": bright_sim,
            "distance_mismatch": dist
        }

    def calculate_crcs(self, rsi, pos_sim, bright_sim, dist_mismatch):
        """
        Calculates the Corneal Reflection Consistency Score (CRCS).
        Range: 0 - 100
        """
        # Linear combination of RSI, position similarity and brightness similarity
        crcs = (rsi * 0.6 + pos_sim * 0.2 + bright_sim * 0.2) * 100
        # Incorporate penalty for larger distance mismatch
        penalty = min(20.0, dist_mismatch * 40.0)
        crcs = max(0.0, min(100.0, crcs - penalty))
        return crcs

    def calculate_ssim(self, l_img, r_img, l_blob, r_blob):
        """
        Calculates the SSIM between left and right reflection regions.
        """
        try:
            # If no reflections are found, return 0.0
            if l_blob is None or r_blob is None:
                return 0.0

            # Bounding boxes for reflection regions in crops
            def get_blob_roi(img, blob):
                # Draw contour on crop and get bounding box with 5px padding
                c = blob["contour"]
                x, y, w, h = cv2.boundingRect(c)
                pad = 5
                x1 = max(0, x - pad)
                y1 = max(0, y - pad)
                x2 = min(img.shape[1], x + w + pad)
                y2 = min(img.shape[0], y + h + pad)
                return img[y1:y2, x1:x2]

            l_roi = get_blob_roi(l_img, l_blob)
            r_roi = get_blob_roi(r_img, r_blob)

            if l_roi.size == 0 or r_roi.size == 0:
                return 0.0

            # Convert to gray
            l_gray = cv2.cvtColor(l_roi, cv2.COLOR_BGR2GRAY)
            r_gray = cv2.cvtColor(r_roi, cv2.COLOR_BGR2GRAY)

            # Resize to match dimensions (average of both)
            h = int((l_gray.shape[0] + r_gray.shape[0]) / 2)
            w = int((l_gray.shape[1] + r_gray.shape[1]) / 2)
            h = max(16, h) # SSIM requires minimal dimension size (e.g. 7x7 window)
            w = max(16, w)

            l_resized = cv2.resize(l_gray, (w, h))
            r_resized = cv2.resize(r_gray, (w, h))

            # Compute SSIM
            win_size = min(7, h, w)
            if win_size % 2 == 0:
                win_size -= 1
            win_size = max(3, win_size)

            score, _ = compare_ssim(l_resized, r_resized, win_size=win_size, full=True)
            return float(max(0.0, min(1.0, score)))
        except Exception as e:
            print(f"[Metrics Calculator] SSIM computation error: {e}")
            return 0.0

    def interpret_rsi(self, rsi):
        if rsi >= 0.90:
            return "Highly Symmetric"
        elif rsi >= 0.70:
            return "Moderately Symmetric"
        else:
            return "Suspicious"

    def interpret_crcs(self, crcs):
        if crcs >= 80:
            return "Real"
        elif crcs >= 50:
            return "Suspicious"
        else:
            return "Deepfake"

    def interpret_trust_score(self, trust_score):
        if trust_score >= 80:
            return "Trustworthy"
        elif trust_score >= 50:
            return "Medium Risk"
        else:
            return "High Risk"
