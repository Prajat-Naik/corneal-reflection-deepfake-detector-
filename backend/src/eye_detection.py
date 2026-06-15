import cv2
import numpy as np
import mediapipe as mp
from mediapipe.python.solutions import face_mesh as mp_face_mesh

class EyeDetector:
    def __init__(self, min_detection_confidence=0.5):
        self.face_mesh = mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=min_detection_confidence
        )
        # Standard landmarks for eyes and irises
        self.LEFT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        self.RIGHT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
        self.LEFT_IRIS = [468, 469, 470, 471, 472]
        self.RIGHT_IRIS = [473, 474, 475, 476, 477]

    def get_mesh_points(self, image):
        """Processes image and extracts all face landmarks scaled to pixel coordinates."""
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_image)
        if not results.multi_face_landmarks:
            return None
        
        h, w = image.shape[:2]
        mesh_points = np.array([
            np.multiply([p.x, p.y], [w, h]).astype(int) 
            for p in results.multi_face_landmarks[0].landmark
        ])
        return mesh_points

    def get_mask_and_crop(self, image, points, iris_indices, eye_indices, padding=1.5):
        """Crops eye region and returns precise circular iris binary mask."""
        # Find Iris Center
        iris_points = points[iris_indices]
        (cx, cy), radius = cv2.minEnclosingCircle(iris_points)
        center = (int(cx), int(cy))
        radius = int(radius)

        # Iris mask on full-size canvas
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.circle(mask, center, radius, 255, -1)

        # Context box from eye contours
        eye_points = points[eye_indices]
        min_x = np.min(eye_points[:, 0])
        max_x = np.max(eye_points[:, 0])
        min_y = np.min(eye_points[:, 1])
        max_y = np.max(eye_points[:, 1])

        w_eye = max_x - min_x
        h_eye = max_y - min_y
        
        px = int(w_eye * (padding - 1) / 2)
        py = int(h_eye * (padding - 1) / 2)
        
        crop_x1 = max(0, min_x - px)
        crop_y1 = max(0, min_y - py)
        crop_x2 = min(image.shape[1], max_x + px)
        crop_y2 = min(image.shape[0], max_y + py)

        eye_crop = image[crop_y1:crop_y2, crop_x1:crop_x2]
        mask_crop = mask[crop_y1:crop_y2, crop_x1:crop_x2]

        return eye_crop, mask_crop, center, radius, (crop_x1, crop_y1, crop_x2, crop_y2)

    def detect_and_crop_eyes(self, image):
        """Processes the face image to extract and return left/right eyes, masks, and landmarks."""
        mesh_points = self.get_mesh_points(image)
        if mesh_points is None:
            return False, {"error": "Failed to extract face landmarks for eye analysis."}

        try:
            # Left Eye Crop
            l_img, l_mask, l_center, l_radius, l_box = self.get_mask_and_crop(
                image, mesh_points, self.LEFT_IRIS, self.LEFT_EYE
            )
            # Right Eye Crop
            r_img, r_mask, r_center, r_radius, r_box = self.get_mask_and_crop(
                image, mesh_points, self.RIGHT_IRIS, self.RIGHT_EYE
            )

            # Draw visual tracking details
            annotated = image.copy()
            cv2.circle(annotated, l_center, l_radius, (0, 255, 0), 2)  # Left circle (green)
            cv2.circle(annotated, r_center, r_radius, (0, 0, 255), 2)  # Right circle (red)

            # Highlight eyelids
            for idx in self.LEFT_EYE:
                cv2.circle(annotated, tuple(mesh_points[idx]), 1, (0, 255, 255), -1)
            for idx in self.RIGHT_EYE:
                cv2.circle(annotated, tuple(mesh_points[idx]), 1, (0, 255, 255), -1)

            return True, {
                "left_img": l_img,
                "left_mask": l_mask,
                "right_img": r_img,
                "right_mask": r_mask,
                "l_center": l_center,
                "r_center": r_center,
                "l_radius": l_radius,
                "r_radius": r_radius,
                "l_box": l_box,
                "r_box": r_box,
                "annotated_mesh": annotated,
                "left_landmarks": [mesh_points[idx].tolist() for idx in self.LEFT_EYE],
                "right_landmarks": [mesh_points[idx].tolist() for idx in self.RIGHT_EYE]
            }
        except Exception as e:
            return False, {"error": f"Failed to align eye landmarks: {str(e)}"}
