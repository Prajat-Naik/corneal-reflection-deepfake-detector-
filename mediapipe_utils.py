import cv2
import mediapipe as mp
from mediapipe.python.solutions import face_mesh as mp_face_mesh
import numpy as np

class IrisTracker:
    def __init__(self):
        self.mp_face_mesh = mp_face_mesh
        # refine_landmarks=True is CRITICAL for Iris landmarks
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )
        
        # Landmark indices (from MediaPipe documentation)
        # Left Eye (Upper/Lower/Corners)
        self.LEFT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        # Right Eye
        self.RIGHT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
        
        # Iris Landmarks (Center is the first index, remaining are the boundary)
        self.LEFT_IRIS = [468, 469, 470, 471, 472]
        self.RIGHT_IRIS = [473, 474, 475, 476, 477]

    def get_mesh_points(self, image):
        """Run Facemesh and return all landmarks as pixel coordinates."""
        results = self.face_mesh.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        if not results.multi_face_landmarks:
            return None
        
        h, w = image.shape[:2]
        mesh_points = np.array([
            np.multiply([p.x, p.y], [w, h]).astype(int) 
            for p in results.multi_face_landmarks[0].landmark
        ])
        return mesh_points

    def get_mask_and_crop(self, image, points, iris_indices, eye_indices, padding=1.5):
        """
        Create a precise binary mask of the iris and crop the eye region.
        
        Args:
            image: Original image.
            points: Full face mesh points.
            iris_indices: Indices for iris landmarks.
            eye_indices: Indices for whole eye landmarks (for cropping context).
            padding: Padding factor for the eye crop.
        """
        # 1. Calculate Iris Center and Radius from landmarks
        iris_points = points[iris_indices]
        (cx, cy), radius = cv2.minEnclosingCircle(iris_points)
        center = (int(cx), int(cy))
        radius = int(radius)

        # 2. Create Full Size Mask
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.circle(mask, center, radius, 255, -1)

        # 3. Determine Eye Crop Region based on eye landmarks (not just iris)
        eye_points = points[eye_indices]
        min_x = np.min(eye_points[:, 0])
        max_x = np.max(eye_points[:, 0])
        min_y = np.min(eye_points[:, 1])
        max_y = np.max(eye_points[:, 1])

        # Add padding
        w_eye = max_x - min_x
        h_eye = max_y - min_y
        
        px = int(w_eye * (padding - 1) / 2)
        py = int(h_eye * (padding - 1) / 2)
        
        crop_x1 = max(0, min_x - px)
        crop_y1 = max(0, min_y - py)
        crop_x2 = min(image.shape[1], max_x + px)
        crop_y2 = min(image.shape[0], max_y + py)

        # 4. Crop Image and Mask
        eye_crop = image[crop_y1:crop_y2, crop_x1:crop_x2]
        mask_crop = mask[crop_y1:crop_y2, crop_x1:crop_x2]

        return eye_crop, mask_crop, center, radius

    def process_image(self, image_path):
        """
        Main function to process an image and return crops + masks.
        Returns:
            (success, data_dict)
            data_dict contains: 
            img_left, mask_left, img_right, mask_right
        """
        image = cv2.imread(image_path)
        if image is None:
            return False, "Image could not be read."

        mesh_points = self.get_mesh_points(image)
        if mesh_points is None:
            return False, "No face detected by MediaPipe."

        data = {}
        
        # Left Eye
        l_img, l_mask, _, _ = self.get_mask_and_crop(
            image, mesh_points, self.LEFT_IRIS, self.LEFT_EYE
        )
        data['left_img'] = l_img
        data['left_mask'] = l_mask.astype(bool) # Convert to boolean as expected by crop_highlights logic

        # Right Eye
        r_img, r_mask, _, _ = self.get_mask_and_crop(
            image, mesh_points, self.RIGHT_IRIS, self.RIGHT_EYE
        )
        data['right_img'] = r_img
        data['right_mask'] = r_mask.astype(bool)

        return True, data
