"""
Face Detection module using OpenCV Haar Cascades and MediaPipe.
Supports detection of faces, counting faces, and determining face positions.
"""

import cv2
import numpy as np
import mediapipe as mp


class FaceDetector:
    """Face detection using Haar Cascades and MediaPipe Face Detection."""

    def __init__(self, min_detection_confidence=0.6):
        """Initialize the face detector.

        Args:
            min_detection_confidence: Minimum confidence threshold for MediaPipe face detection.
        """
        # Haar Cascade
        self.haar_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        # MediaPipe Face Detection
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=1,
            min_detection_confidence=min_detection_confidence,
        )
        self.mp_drawing = mp.solutions.drawing_utils

    def detect_faces_haar(self, frame):
        """Detect faces using Haar Cascade classifier.

        Args:
            frame: BGR image as numpy array.

        Returns:
            List of face bounding boxes as (x, y, w, h) tuples.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.haar_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(60, 60),
            flags=cv2.CASCADE_SCALE_IMAGE,
        )
        return faces if len(faces) > 0 else []

    def detect_faces_mediapipe(self, frame):
        """Detect faces using MediaPipe Face Detection.

        Args:
            frame: BGR image as numpy array.

        Returns:
            List of dictionaries with 'bbox', 'confidence', and 'keypoints'.
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(rgb_frame)

        faces = []
        if results.detections:
            h, w, _ = frame.shape
            for detection in results.detections:
                bbox = detection.location_data.relative_bounding_box
                x = int(bbox.xmin * w)
                y = int(bbox.ymin * h)
                bw = int(bbox.width * w)
                bh = int(bbox.height * h)

                # Clamp to frame boundaries
                x = max(0, x)
                y = max(0, y)
                bw = min(bw, w - x)
                bh = min(bh, h - y)

                confidence = detection.score[0] if detection.score else 0.0

                keypoints = {}
                for idx, kp in enumerate(detection.location_data.relative_keypoints):
                    keypoints[idx] = (int(kp.x * w), int(kp.y * h))

                faces.append({
                    "bbox": (x, y, bw, bh),
                    "confidence": confidence,
                    "keypoints": keypoints,
                })

        return faces

    def detect_faces(self, frame):
        """Primary face detection method. Uses MediaPipe with Haar Cascade as fallback.

        Args:
            frame: BGR image as numpy array.

        Returns:
            Tuple of (face_count, faces_data, detection_method).
        """
        # Try MediaPipe first
        mp_faces = self.detect_faces_mediapipe(frame)
        if mp_faces:
            return len(mp_faces), mp_faces, "mediapipe"

        # Fallback to Haar Cascade
        haar_faces = self.detect_faces_haar(frame)
        if len(haar_faces) > 0:
            faces_data = []
            for (x, y, w, h) in haar_faces:
                faces_data.append({
                    "bbox": (x, y, w, h),
                    "confidence": 0.8,
                    "keypoints": {},
                })
            return len(haar_faces), faces_data, "haar"

        return 0, [], "none"

    def check_multiple_faces(self, frame):
        """Check if multiple faces are detected.

        Args:
            frame: BGR image as numpy array.

        Returns:
            Tuple of (is_multiple, face_count, confidence).
        """
        face_count, faces_data, method = self.detect_faces(frame)
        if face_count > 1:
            avg_confidence = np.mean([f["confidence"] for f in faces_data])
            return True, face_count, float(avg_confidence)
        return False, face_count, 0.0

    def check_face_missing(self, frame):
        """Check if no face is detected.

        Args:
            frame: BGR image as numpy array.

        Returns:
            Tuple of (is_missing, confidence).
        """
        face_count, faces_data, method = self.detect_faces(frame)
        if face_count == 0:
            return True, 1.0
        return False, 0.0

    def get_face_region(self, frame):
        """Extract the face region from the frame.

        Args:
            frame: BGR image as numpy array.

        Returns:
            Face region as numpy array or None.
        """
        face_count, faces_data, method = self.detect_faces(frame)
        if face_count > 0:
            x, y, w, h = faces_data[0]["bbox"]
            return frame[y:y+h, x:x+w]
        return None

    def draw_detections(self, frame, faces_data):
        """Draw face detections on the frame.

        Args:
            frame: BGR image as numpy array.
            faces_data: List of face data dictionaries.

        Returns:
            Frame with detections drawn.
        """
        annotated = frame.copy()
        for face in faces_data:
            x, y, w, h = face["bbox"]
            confidence = face.get("confidence", 0)
            color = (0, 255, 0) if confidence > 0.7 else (0, 165, 255)
            cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
            label = f"Face: {confidence:.1%}"
            cv2.putText(
                annotated, label, (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2
            )
        return annotated

    def release(self):
        """Release resources."""
        self.face_detection.close()
