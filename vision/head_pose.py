"""
Head Pose Estimation module using MediaPipe Face Mesh.
Estimates yaw, pitch, and roll of the head to detect looking away.
"""

import cv2
import numpy as np
import mediapipe as mp


class HeadPoseEstimator:
    """Head pose estimation using MediaPipe Face Mesh and solvePnP."""

    # 3D model points of a generic face (canonical face model)
    MODEL_POINTS = np.array([
        (0.0, 0.0, 0.0),          # Nose tip
        (0.0, -330.0, -65.0),     # Chin
        (-225.0, 170.0, -135.0),  # Left eye left corner
        (225.0, 170.0, -135.0),   # Right eye right corner
        (-150.0, -150.0, -125.0), # Left mouth corner
        (150.0, -150.0, -125.0),  # Right mouth corner
    ], dtype=np.float64)

    # MediaPipe Face Mesh landmark indices corresponding to the 3D model points
    LANDMARK_INDICES = [1, 152, 33, 263, 61, 291]

    def __init__(self, yaw_threshold=30.0, pitch_threshold=25.0):
        """Initialize head pose estimator.

        Args:
            yaw_threshold: Maximum allowed yaw angle (degrees).
            pitch_threshold: Maximum allowed pitch angle (degrees).
        """
        self.yaw_threshold = yaw_threshold
        self.pitch_threshold = pitch_threshold

        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    def estimate_pose(self, frame):
        """Estimate head pose from a frame.

        Args:
            frame: BGR image as numpy array.

        Returns:
            Dictionary with 'yaw', 'pitch', 'roll', 'is_looking_away',
            'direction', and 'confidence', or None if no face.
        """
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)

        if not results.multi_face_landmarks:
            return None

        face_landmarks = results.multi_face_landmarks[0]

        # Extract 2D image points
        image_points = np.array([
            (face_landmarks.landmark[idx].x * w, face_landmarks.landmark[idx].y * h)
            for idx in self.LANDMARK_INDICES
        ], dtype=np.float64)

        # Camera internals (approximate)
        focal_length = w
        center = (w / 2, h / 2)
        camera_matrix = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1],
        ], dtype=np.float64)
        dist_coeffs = np.zeros((4, 1))

        # Solve PnP
        success, rotation_vector, translation_vector = cv2.solvePnP(
            self.MODEL_POINTS,
            image_points,
            camera_matrix,
            dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE,
        )

        if not success:
            return None

        # Convert rotation vector to rotation matrix
        rotation_matrix, _ = cv2.Rodrigues(rotation_vector)

        # Decompose rotation matrix to Euler angles
        proj_matrix = np.hstack((rotation_matrix, translation_vector))
        euler_angles = cv2.decomposeProjectionMatrix(proj_matrix)[6]

        pitch = float(euler_angles[0])
        yaw = float(euler_angles[1])
        roll = float(euler_angles[2])

        # Normalize angles
        pitch = self._normalize_angle(pitch)
        yaw = self._normalize_angle(yaw)
        roll = self._normalize_angle(roll)

        # Determine if looking away
        is_looking_away = abs(yaw) > self.yaw_threshold or abs(pitch) > self.pitch_threshold

        # Determine direction
        direction = self._get_direction(yaw, pitch)

        # Confidence based on how far from threshold
        if is_looking_away:
            max_deviation = max(
                abs(yaw) / self.yaw_threshold if abs(yaw) > self.yaw_threshold else 0,
                abs(pitch) / self.pitch_threshold if abs(pitch) > self.pitch_threshold else 0,
            )
            confidence = min(1.0, max_deviation - 1.0 + 0.5)
        else:
            confidence = 0.0

        return {
            "yaw": round(yaw, 2),
            "pitch": round(pitch, 2),
            "roll": round(roll, 2),
            "is_looking_away": is_looking_away,
            "direction": direction,
            "confidence": round(confidence, 2),
        }

    def _normalize_angle(self, angle):
        """Normalize angle to [-180, 180] range."""
        while angle > 180:
            angle -= 360
        while angle < -180:
            angle += 360
        return angle

    def _get_direction(self, yaw, pitch):
        """Determine the direction the person is looking."""
        directions = []
        if yaw < -self.yaw_threshold:
            directions.append("left")
        elif yaw > self.yaw_threshold:
            directions.append("right")
        if pitch < -self.pitch_threshold:
            directions.append("down")
        elif pitch > self.pitch_threshold:
            directions.append("up")
        return ", ".join(directions) if directions else "center"

    def release(self):
        """Release resources."""
        self.face_mesh.close()
