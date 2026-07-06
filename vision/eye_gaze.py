"""
Eye Gaze Detection module using MediaPipe Face Mesh.
Detects eye gaze direction and blink rate.
"""

import cv2
import numpy as np
import mediapipe as mp


class EyeGazeDetector:
    """Eye gaze and blink detection using MediaPipe Face Mesh iris landmarks."""

    # Landmark indices for eye regions
    LEFT_EYE = [362, 385, 387, 263, 373, 380]
    RIGHT_EYE = [33, 160, 158, 133, 153, 144]

    # Iris landmarks (refined landmarks must be enabled)
    LEFT_IRIS = [474, 475, 476, 477]
    RIGHT_IRIS = [469, 470, 471, 472]

    # Eye aspect ratio threshold for blink detection
    EAR_THRESHOLD = 0.21
    CONSECUTIVE_FRAMES_FOR_BLINK = 3

    def __init__(self, gaze_threshold=0.25):
        """Initialize eye gaze detector.

        Args:
            gaze_threshold: Threshold for gaze deviation (0-1 range).
        """
        self.gaze_threshold = gaze_threshold
        self.blink_counter = 0
        self.total_blinks = 0
        self.frame_count = 0

        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    def detect_gaze(self, frame):
        """Detect eye gaze direction.

        Args:
            frame: BGR image as numpy array.

        Returns:
            Dictionary with gaze analysis results, or None if no face.
        """
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)

        if not results.multi_face_landmarks:
            return None

        face_landmarks = results.multi_face_landmarks[0]
        landmarks = face_landmarks.landmark

        # Calculate Eye Aspect Ratio (EAR) for blink detection
        left_ear = self._calculate_ear(landmarks, self.LEFT_EYE, w, h)
        right_ear = self._calculate_ear(landmarks, self.RIGHT_EYE, w, h)
        avg_ear = (left_ear + right_ear) / 2.0

        # Blink detection
        is_blinking = avg_ear < self.EAR_THRESHOLD
        if is_blinking:
            self.blink_counter += 1
        else:
            if self.blink_counter >= self.CONSECUTIVE_FRAMES_FOR_BLINK:
                self.total_blinks += 1
            self.blink_counter = 0

        self.frame_count += 1

        # Gaze direction using iris position relative to eye boundaries
        left_gaze_ratio = self._calculate_gaze_ratio(
            landmarks, self.LEFT_EYE, self.LEFT_IRIS, w, h
        )
        right_gaze_ratio = self._calculate_gaze_ratio(
            landmarks, self.RIGHT_EYE, self.RIGHT_IRIS, w, h
        )
        avg_gaze_ratio = (left_gaze_ratio + right_gaze_ratio) / 2.0

        # Determine gaze direction
        gaze_direction = self._get_gaze_direction(avg_gaze_ratio)

        # Check if gaze is suspicious
        is_suspicious = abs(avg_gaze_ratio - 0.5) > self.gaze_threshold

        confidence = min(1.0, abs(avg_gaze_ratio - 0.5) / self.gaze_threshold) if is_suspicious else 0.0

        return {
            "gaze_ratio": round(avg_gaze_ratio, 3),
            "gaze_direction": gaze_direction,
            "is_suspicious": is_suspicious,
            "confidence": round(confidence, 2),
            "ear": round(avg_ear, 3),
            "is_blinking": is_blinking,
            "total_blinks": self.total_blinks,
            "blink_rate": round(self.total_blinks / max(1, self.frame_count) * 30, 1),
        }

    def _calculate_ear(self, landmarks, eye_indices, w, h):
        """Calculate Eye Aspect Ratio.

        Args:
            landmarks: Face mesh landmarks.
            eye_indices: Indices for the 6 eye landmarks.
            w: Frame width.
            h: Frame height.

        Returns:
            Eye aspect ratio float value.
        """
        points = np.array([
            (landmarks[idx].x * w, landmarks[idx].y * h) for idx in eye_indices
        ])

        # Vertical distances
        v1 = np.linalg.norm(points[1] - points[5])
        v2 = np.linalg.norm(points[2] - points[4])

        # Horizontal distance
        h1 = np.linalg.norm(points[0] - points[3])

        if h1 == 0:
            return 0.0

        ear = (v1 + v2) / (2.0 * h1)
        return ear

    def _calculate_gaze_ratio(self, landmarks, eye_indices, iris_indices, w, h):
        """Calculate gaze ratio based on iris position within the eye.

        Args:
            landmarks: Face mesh landmarks.
            eye_indices: Indices for the eye boundary landmarks.
            iris_indices: Indices for the iris landmarks.
            w: Frame width.
            h: Frame height.

        Returns:
            Gaze ratio (0.0 = looking right, 0.5 = center, 1.0 = looking left).
        """
        # Eye boundary
        eye_points = np.array([
            (landmarks[idx].x * w, landmarks[idx].y * h) for idx in eye_indices
        ])

        # Iris center
        iris_points = np.array([
            (landmarks[idx].x * w, landmarks[idx].y * h) for idx in iris_indices
        ])
        iris_center = iris_points.mean(axis=0)

        # Eye horizontal range
        eye_left = eye_points[:, 0].min()
        eye_right = eye_points[:, 0].max()
        eye_width = eye_right - eye_left

        if eye_width == 0:
            return 0.5

        # Calculate ratio
        ratio = (iris_center[0] - eye_left) / eye_width
        return max(0.0, min(1.0, ratio))

    def _get_gaze_direction(self, gaze_ratio):
        """Determine gaze direction from ratio.

        Args:
            gaze_ratio: Gaze ratio (0-1).

        Returns:
            String describing gaze direction.
        """
        if gaze_ratio < 0.5 - self.gaze_threshold:
            return "looking_left"
        elif gaze_ratio > 0.5 + self.gaze_threshold:
            return "looking_right"
        return "center"

    def reset_blink_counter(self):
        """Reset blink counting statistics."""
        self.blink_counter = 0
        self.total_blinks = 0
        self.frame_count = 0

    def release(self):
        """Release resources."""
        self.face_mesh.close()
