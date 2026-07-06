"""
Proctoring Engine — the main orchestrator that combines all vision modules
to analyze frames and produce violation events.
"""

import cv2
import numpy as np
import base64
import os
import time
from datetime import datetime

from vision.face_detector import FaceDetector
from vision.face_recognizer import FaceRecognizer
from vision.head_pose import HeadPoseEstimator
from vision.eye_gaze import EyeGazeDetector
from vision.blur_detector import BlurDetector
from vision.phone_detector import PhoneDetector


class ProctoringEngine:
    """Central proctoring engine that runs all vision checks on each frame."""

    VIOLATION_TYPES = {
        "face_missing": "Face Not Detected",
        "multiple_faces": "Multiple Faces Detected",
        "unknown_face": "Unknown Face Detected",
        "face_blur": "Face is Blurry / Obstructed",
        "head_pose": "Looking Away from Screen",
        "eye_gaze": "Suspicious Eye Movement",
        "phone_detected": "Mobile Phone Detected",
        "tab_switch": "Tab / Window Switched",
        "fullscreen_exit": "Exited Full Screen",
        "copy_paste": "Copy / Paste Attempted",
        "right_click": "Right Click Attempted",
        "keyboard_shortcut": "Blocked Keyboard Shortcut",
        "exam_terminated": "Exam Auto-Terminated",
    }

    def __init__(self, config):
        """Initialize proctoring engine with all vision modules.

        Args:
            config: Application config object.
        """
        self.config = config

        self.face_detector = FaceDetector(
            min_detection_confidence=config.get("FACE_DETECTION_CONFIDENCE", 0.6)
        )
        self.face_recognizer = FaceRecognizer(
            tolerance=config.get("FACE_RECOGNITION_TOLERANCE", 0.5)
        )
        self.head_pose_estimator = HeadPoseEstimator(
            yaw_threshold=config.get("HEAD_POSE_YAW_THRESHOLD", 30.0),
            pitch_threshold=config.get("HEAD_POSE_PITCH_THRESHOLD", 25.0),
        )
        self.eye_gaze_detector = EyeGazeDetector(
            gaze_threshold=config.get("EYE_GAZE_THRESHOLD", 0.25)
        )
        self.blur_detector = BlurDetector(
            threshold=config.get("BLUR_THRESHOLD", 80.0)
        )
        self.phone_detector = PhoneDetector(
            config_path=config.get("YOLO_CONFIG"),
            weights_path=config.get("YOLO_WEIGHTS"),
            classes_path=config.get("YOLO_CLASSES"),
            confidence_threshold=config.get("PHONE_DETECTION_CONFIDENCE", 0.45),
        )

        # Cooldown tracking (to avoid spamming same violation type)
        self._last_violation_time = {}
        self._cooldown_seconds = 5  # Minimum seconds between same violation type

    def analyze_frame(self, frame_base64, stored_encoding=None):
        """Analyze a single frame for all proctoring violations.

        Args:
            frame_base64: Base64-encoded frame image.
            stored_encoding: The registered student's face encoding (numpy array).

        Returns:
            Dictionary with analysis results and any detected violations.
        """
        # Decode frame
        frame = self._decode_frame(frame_base64)
        if frame is None:
            return {"success": False, "error": "Failed to decode frame"}

        violations = []
        analysis = {
            "success": True,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "violations": [],
            "face_detected": False,
            "face_count": 0,
        }

        # 1. Face Detection — missing / multiple
        face_count, faces_data, detection_method = self.face_detector.detect_faces(frame)
        analysis["face_count"] = face_count
        analysis["face_detected"] = face_count > 0

        if face_count == 0:
            violation = self._create_violation(
                "face_missing", 1.0,
                "No face detected in the camera feed."
            )
            if violation:
                violations.append(violation)

        elif face_count > 1:
            violation = self._create_violation(
                "multiple_faces", 0.9,
                f"{face_count} faces detected in the camera feed."
            )
            if violation:
                violations.append(violation)

        # Only run detailed checks if exactly one face is detected
        if face_count >= 1:
            face_bbox = faces_data[0]["bbox"] if faces_data else None

            # 2. Face Recognition — unknown face
            if stored_encoding is not None:
                is_unknown, confidence, _ = self.face_recognizer.check_unknown_face(frame, stored_encoding)
                if is_unknown:
                    violation = self._create_violation(
                        "unknown_face", confidence,
                        "An unregistered face has been detected."
                    )
                    if violation:
                        violations.append(violation)

            # 3. Face Blur Detection
            if face_bbox:
                is_blurry, blur_score, confidence = self.blur_detector.check_face_blur(frame, face_bbox)
                if is_blurry:
                    violation = self._create_violation(
                        "face_blur", confidence,
                        f"Face region is blurry (score: {blur_score})."
                    )
                    if violation:
                        violations.append(violation)

            # 4. Head Pose Estimation
            pose_result = self.head_pose_estimator.estimate_pose(frame)
            if pose_result and pose_result["is_looking_away"]:
                violation = self._create_violation(
                    "head_pose", pose_result["confidence"],
                    f"Looking {pose_result['direction']} (yaw: {pose_result['yaw']}°, pitch: {pose_result['pitch']}°)."
                )
                if violation:
                    violations.append(violation)
                analysis["head_pose"] = pose_result

            # 5. Eye Gaze Detection
            gaze_result = self.eye_gaze_detector.detect_gaze(frame)
            if gaze_result and gaze_result["is_suspicious"]:
                violation = self._create_violation(
                    "eye_gaze", gaze_result["confidence"],
                    f"Suspicious eye movement: {gaze_result['gaze_direction']}."
                )
                if violation:
                    violations.append(violation)
                analysis["eye_gaze"] = gaze_result

        # 6. Phone Detection
        phone_detected, phone_confidence, phone_bbox = self.phone_detector.detect_phone(frame)
        if phone_detected:
            violation = self._create_violation(
                "phone_detected", phone_confidence,
                "Mobile phone detected in the camera feed."
            )
            if violation:
                violations.append(violation)

        analysis["violations"] = violations
        return analysis

    def _create_violation(self, violation_type, confidence, description):
        """Create a violation dict if cooldown has elapsed.

        Args:
            violation_type: Type identifier string.
            confidence: Confidence score (0-1).
            description: Human-readable description.

        Returns:
            Violation dict or None if still in cooldown.
        """
        now = time.time()
        last_time = self._last_violation_time.get(violation_type, 0)

        if now - last_time < self._cooldown_seconds:
            return None

        self._last_violation_time[violation_type] = now

        return {
            "type": violation_type,
            "label": self.VIOLATION_TYPES.get(violation_type, violation_type),
            "confidence": round(confidence, 2),
            "description": description,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def create_browser_violation(self, violation_type, description=""):
        """Create a violation from browser events (tab switch, copy/paste, etc.).

        Args:
            violation_type: Type identifier string.
            description: Description of the violation.

        Returns:
            Violation dict or None.
        """
        confidence = 1.0
        if not description:
            description = self.VIOLATION_TYPES.get(violation_type, violation_type)
        return self._create_violation(violation_type, confidence, description)

    def _decode_frame(self, frame_base64):
        """Decode a base64-encoded frame.

        Args:
            frame_base64: Base64 string (with or without data URI prefix).

        Returns:
            Numpy array (BGR) or None.
        """
        try:
            if "," in frame_base64:
                frame_base64 = frame_base64.split(",")[1]
            img_bytes = base64.b64decode(frame_base64)
            np_arr = np.frombuffer(img_bytes, dtype=np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            return frame
        except Exception:
            return None

    def save_screenshot(self, frame_base64, save_dir, student_id, violation_type):
        """Save a screenshot from base64 frame data.

        Args:
            frame_base64: Base64-encoded frame.
            save_dir: Directory to save screenshots.
            student_id: Student identifier.
            violation_type: Type of violation.

        Returns:
            Saved file path or None.
        """
        try:
            frame = self._decode_frame(frame_base64)
            if frame is None:
                return None

            os.makedirs(save_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{student_id}_{violation_type}_{timestamp}.jpg"
            filepath = os.path.join(save_dir, filename)

            cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            return filepath
        except Exception:
            return None

    def release(self):
        """Release all vision module resources."""
        self.face_detector.release()
        self.head_pose_estimator.release()
        self.eye_gaze_detector.release()
