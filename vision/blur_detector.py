"""
Face Blur Detection module.
Detects if the face in the camera feed is blurry (camera obstruction, out of focus).
"""

import cv2
import numpy as np


class BlurDetector:
    """Detect blurriness in face regions using Laplacian variance."""

    def __init__(self, threshold=80.0):
        """Initialize blur detector.

        Args:
            threshold: Laplacian variance threshold below which image is considered blurry.
        """
        self.threshold = threshold

    def calculate_blur_score(self, image):
        """Calculate blur score using Laplacian variance.

        Args:
            image: Image as numpy array (BGR or grayscale).

        Returns:
            Blur score (higher = sharper, lower = blurrier).
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        score = laplacian.var()
        return float(score)

    def is_blurry(self, image):
        """Check if an image is blurry.

        Args:
            image: Image as numpy array.

        Returns:
            Tuple of (is_blurry, blur_score, confidence).
        """
        score = self.calculate_blur_score(image)
        blurry = score < self.threshold

        if blurry:
            # Confidence increases as blur score decreases
            confidence = min(1.0, max(0.0, 1.0 - (score / self.threshold)))
        else:
            confidence = 0.0

        return blurry, round(score, 2), round(confidence, 2)

    def check_face_blur(self, frame, face_bbox=None):
        """Check if the face region in the frame is blurry.

        Args:
            frame: BGR image as numpy array.
            face_bbox: Optional tuple (x, y, w, h) of the face bounding box.
                       If None, checks the entire frame.

        Returns:
            Tuple of (is_blurry, blur_score, confidence).
        """
        if face_bbox is not None:
            x, y, w, h = face_bbox
            # Ensure bounds are valid
            x = max(0, x)
            y = max(0, y)
            fh, fw = frame.shape[:2]
            w = min(w, fw - x)
            h = min(h, fh - y)
            if w <= 0 or h <= 0:
                return False, 0.0, 0.0
            face_region = frame[y:y+h, x:x+w]
        else:
            face_region = frame

        if face_region.size == 0:
            return False, 0.0, 0.0

        return self.is_blurry(face_region)
