"""
Face Recognition module using the face_recognition library.
Handles face encoding generation, storage, and verification.
"""

import os
import pickle
import cv2
import numpy as np
import face_recognition


class FaceRecognizer:
    """Face recognition using dlib-based face_recognition library."""

    def __init__(self, tolerance=0.5):
        """Initialize the face recognizer.

        Args:
            tolerance: Distance tolerance for face matching (lower = stricter).
        """
        self.tolerance = tolerance

    def generate_encoding(self, image):
        """Generate face encoding from an image.

        Args:
            image: BGR image as numpy array (OpenCV format).

        Returns:
            Tuple of (encoding, success, message).
        """
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Detect face locations
        face_locations = face_recognition.face_locations(rgb_image, model="hog")

        if len(face_locations) == 0:
            return None, False, "No face detected in the image."

        if len(face_locations) > 1:
            return None, False, "Multiple faces detected. Please ensure only your face is visible."

        # Generate encoding
        encodings = face_recognition.face_encodings(rgb_image, face_locations)
        if len(encodings) == 0:
            return None, False, "Could not generate face encoding."

        return encodings[0], True, "Face encoding generated successfully."

    def save_encoding(self, encoding, file_path):
        """Save face encoding to a file.

        Args:
            encoding: Face encoding numpy array.
            file_path: Path to save the encoding file.

        Returns:
            Boolean indicating success.
        """
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "wb") as f:
                pickle.dump(encoding, f)
            return True
        except Exception:
            return False

    def load_encoding(self, file_path):
        """Load face encoding from a file.

        Args:
            file_path: Path to the encoding file.

        Returns:
            Face encoding numpy array or None.
        """
        try:
            with open(file_path, "rb") as f:
                return pickle.load(f)
        except Exception:
            return None

    def verify_face(self, frame, stored_encoding):
        """Verify if the face in the frame matches the stored encoding.

        Args:
            frame: BGR image as numpy array.
            stored_encoding: Stored face encoding numpy array.

        Returns:
            Tuple of (is_match, confidence, message).
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame, model="hog")

        if len(face_locations) == 0:
            return False, 0.0, "No face detected."

        encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        if len(encodings) == 0:
            return False, 0.0, "Could not generate face encoding for verification."

        # Compare with stored encoding
        for encoding in encodings:
            distance = face_recognition.face_distance([stored_encoding], encoding)[0]
            confidence = max(0.0, 1.0 - distance)

            if distance <= self.tolerance:
                return True, float(confidence), "Face verified successfully."

        return False, float(1.0 - distance), "Face does not match registered face."

    def check_unknown_face(self, frame, stored_encoding):
        """Check if the face in the frame is unknown (doesn't match stored encoding).

        Args:
            frame: BGR image as numpy array.
            stored_encoding: Stored face encoding numpy array.

        Returns:
            Tuple of (is_unknown, confidence, face_count).
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame, model="hog")

        if len(face_locations) == 0:
            return False, 0.0, 0

        encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        unknown_faces = 0

        for encoding in encodings:
            distance = face_recognition.face_distance([stored_encoding], encoding)[0]
            if distance > self.tolerance:
                unknown_faces += 1

        if unknown_faces > 0:
            confidence = min(1.0, unknown_faces / len(encodings))
            return True, float(confidence), len(face_locations)

        return False, 0.0, len(face_locations)

    def generate_encoding_from_file(self, image_path):
        """Generate face encoding from an image file path.

        Args:
            image_path: Path to the image file.

        Returns:
            Tuple of (encoding, success, message).
        """
        image = cv2.imread(image_path)
        if image is None:
            return None, False, "Could not read image file."
        return self.generate_encoding(image)
