import cv2
import numpy as np

class SpecularReflectionExtractor:
    def __init__(self, adaptive_method=cv2.ADAPTIVE_THRESH_GAUSSIAN_C, block_size=11, C=2):
        self.adaptive_method = adaptive_method
        self.block_size = block_size
        self.C = C

    def extract_highlights(self, eye_crop, iris_mask):
        """
        Extracts corneal reflection specular highlights using the research pipeline.
        
        Steps:
        1. Grayscale conversion.
        2. Contrast enhancement via CLAHE histogram equalization.
        3. Adaptive Thresholding inside the iris boundary.
        4. Morphological filters to clear noise.
        5. Contour/Blob extraction for position, area, and brightness.
        """
        # Step 1: Grayscale conversion
        gray = cv2.cvtColor(eye_crop, cv2.COLOR_BGR2GRAY)

        # Step 2: Histogram Equalization (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        equalized = clahe.apply(gray)

        # Step 3: Adaptive Thresholding
        binary = cv2.adaptiveThreshold(
            equalized, 255, self.adaptive_method, cv2.THRESH_BINARY, self.block_size, self.C
        )

        # Mask output to only search within the iris bounds
        binary_iris = cv2.bitwise_and(binary, iris_mask)

        # Step 4: Morphological Operations (Opening to clear noise, Closing to fill holes)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        morphed = cv2.morphologyEx(binary_iris, cv2.MORPH_OPEN, kernel)
        morphed = cv2.morphologyEx(morphed, cv2.MORPH_CLOSE, kernel)

        # Step 5: Contour Detection
        contours, _ = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Step 6: Reflection Blob Extraction
        blobs = []
        for c in contours:
            area = cv2.contourArea(c)
            if area < 1.0: # Ignore noise/single pixels
                continue

            # Centroid calculations via moments
            M = cv2.moments(c)
            if M["m00"] != 0:
                cx = float(M["m10"] / M["m00"])
                cy = float(M["m01"] / M["m00"])
            else:
                # Fallback to bounding rect center
                bx, by, bw, bh = cv2.boundingRect(c)
                cx = bx + bw / 2.0
                cy = by + bh / 2.0

            # Brightness calculation: average intensity in grayscale
            mask = np.zeros_like(gray)
            cv2.drawContours(mask, [c], -1, 255, -1)
            mean_intensity = cv2.mean(gray, mask=mask)[0]

            blobs.append({
                "contour": c,
                "position": (cx, cy),
                "area": area,
                "brightness": mean_intensity
            })

        # Sort blobs by area descending so the largest reflection is primary
        blobs = sorted(blobs, key=lambda x: x["area"], reverse=True)

        return morphed, blobs
