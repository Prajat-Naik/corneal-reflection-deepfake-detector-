import cv2
import mediapipe as mp
from mediapipe.python.solutions import face_detection as mp_face_detection

class FaceDetector:
    def __init__(self, min_detection_confidence=0.5):
        self.face_detector = mp_face_detection.FaceDetection(
            min_detection_confidence=min_detection_confidence
        )

    def detect_face(self, image):
        """
        Detects the primary face in the image, draws high-quality tech bounding boxes, and crops the region.
        """
        h, w, _ = image.shape
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.face_detector.process(rgb_image)

        if not results.detections:
            return False, {"error": "No face detected in the image."}

        # Select the primary (largest) face bounding box
        largest_area = 0
        primary_detection = None
        face_confidence = 0.0

        for detection in results.detections:
            bbox = detection.location_data.relative_bounding_box
            area = bbox.width * bbox.height
            if area > largest_area:
                largest_area = area
                primary_detection = bbox
                face_confidence = detection.score[0] if detection.score else 0.0

        if primary_detection is None:
            return False, {"error": "Failed to extract primary face."}

        # Absolute coordinates with padding
        x_min = int(primary_detection.xmin * w)
        y_min = int(primary_detection.ymin * h)
        bbox_w = int(primary_detection.width * w)
        bbox_h = int(primary_detection.height * h)

        pad_w = int(bbox_w * 0.15)
        pad_h = int(bbox_h * 0.15)

        x1 = max(0, x_min - pad_w)
        y1 = max(0, y_min - pad_h)
        x2 = min(w, x_min + bbox_w + pad_w)
        y2 = min(h, y_min + bbox_h + pad_h)

        face_crop = image[y1:y2, x1:x2]

        # Annotated image with neon borders
        annotated_image = image.copy()
        color = (241, 102, 99) # BGR Neon Indigo
        thickness = 3
        cv2.rectangle(annotated_image, (x_min, y_min), (x_min + bbox_w, y_min + bbox_h), color, thickness)
        
        # Tech corners
        length = int(min(bbox_w, bbox_h) * 0.15)
        # Top-left corner
        cv2.line(annotated_image, (x_min, y_min), (x_min + length, y_min), color, thickness + 2)
        cv2.line(annotated_image, (x_min, y_min), (x_min, y_min + length), color, thickness + 2)
        # Top-right corner
        cv2.line(annotated_image, (x_min + bbox_w, y_min), (x_min + bbox_w - length, y_min), color, thickness + 2)
        cv2.line(annotated_image, (x_min + bbox_w, y_min), (x_min + bbox_w, y_min + length), color, thickness + 2)
        # Bottom-left corner
        cv2.line(annotated_image, (x_min, y_min + bbox_h), (x_min + length, y_min + bbox_h), color, thickness + 2)
        cv2.line(annotated_image, (x_min, y_min + bbox_h), (x_min, y_min + bbox_h - length), color, thickness + 2)
        # Bottom-right corner
        cv2.line(annotated_image, (x_min + bbox_w, y_min + bbox_h), (x_min + bbox_w - length, y_min + bbox_h), color, thickness + 2)
        cv2.line(annotated_image, (x_min + bbox_w, y_min + bbox_h), (x_min + bbox_w, y_min + bbox_h - length), color, thickness + 2)

        return True, {
            "bbox": (x_min, y_min, bbox_w, bbox_h),
            "crop": face_crop,
            "annotated_image": annotated_image,
            "confidence": face_confidence,
            "coords_str": f"X: {x_min}, Y: {y_min}, W: {bbox_w}, H: {bbox_h}"
        }
