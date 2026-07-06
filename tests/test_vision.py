"""
Tests for computer vision modules — face detection, blur detection, head pose.
These tests use synthetic images to avoid requiring a webcam.
"""

import unittest
import sys
import os
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestBlurDetector(unittest.TestCase):
    """Test suite for BlurDetector."""

    def setUp(self):
        """Set up test fixtures."""
        from vision.blur_detector import BlurDetector
        self.detector = BlurDetector(threshold=80.0)

    def test_sharp_image_not_blurry(self):
        """Test that a sharp synthetic image is not detected as blurry."""
        # Create a checkerboard pattern (high-frequency = sharp)
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        for i in range(0, 200, 10):
            for j in range(0, 200, 10):
                if (i // 10 + j // 10) % 2 == 0:
                    img[i:i+10, j:j+10] = [255, 255, 255]

        is_blurry, score, confidence = self.detector.is_blurry(img)
        self.assertFalse(is_blurry)
        self.assertGreater(score, 80.0)

    def test_blurry_image_detected(self):
        """Test that a uniform (blurry) image is detected as blurry."""
        # Create a uniform gray image (no edges = very blurry)
        img = np.ones((200, 200, 3), dtype=np.uint8) * 128

        is_blurry, score, confidence = self.detector.is_blurry(img)
        self.assertTrue(is_blurry)
        self.assertLess(score, 80.0)

    def test_blur_score_calculation(self):
        """Test blur score is a valid float."""
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        score = self.detector.calculate_blur_score(img)
        self.assertIsInstance(score, float)
        self.assertGreater(score, 0)

    def test_check_face_blur_full_frame(self):
        """Test face blur check on full frame (no bbox)."""
        img = np.ones((200, 200, 3), dtype=np.uint8) * 128
        is_blurry, score, confidence = self.detector.check_face_blur(img)
        self.assertIsInstance(is_blurry, bool)
        self.assertIsInstance(score, float)

    def test_check_face_blur_with_bbox(self):
        """Test face blur check with bounding box."""
        img = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
        is_blurry, score, confidence = self.detector.check_face_blur(img, (50, 50, 100, 100))
        self.assertIsInstance(is_blurry, bool)
        self.assertIsInstance(score, float)

    def test_empty_region(self):
        """Test with zero-size region."""
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        is_blurry, score, confidence = self.detector.check_face_blur(img, (0, 0, 0, 0))
        self.assertFalse(is_blurry)


class TestFaceDetector(unittest.TestCase):
    """Test suite for FaceDetector — basic initialization and synthetic image tests."""

    def test_initialization(self):
        """Test FaceDetector initializes without errors."""
        from vision.face_detector import FaceDetector
        detector = FaceDetector(min_detection_confidence=0.6)
        self.assertIsNotNone(detector)
        self.assertIsNotNone(detector.haar_cascade)
        detector.release()

    def test_detect_no_face_in_blank(self):
        """Test that no face is detected in a blank image."""
        from vision.face_detector import FaceDetector
        detector = FaceDetector(min_detection_confidence=0.6)
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        face_count, faces_data, method = detector.detect_faces(blank)
        self.assertEqual(face_count, 0)
        self.assertEqual(len(faces_data), 0)
        detector.release()

    def test_check_face_missing_blank(self):
        """Test face missing check on blank image."""
        from vision.face_detector import FaceDetector
        detector = FaceDetector()
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        is_missing, confidence = detector.check_face_missing(blank)
        self.assertTrue(is_missing)
        detector.release()

    def test_check_multiple_faces_blank(self):
        """Test multiple faces check on blank image."""
        from vision.face_detector import FaceDetector
        detector = FaceDetector()
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        is_multiple, count, confidence = detector.check_multiple_faces(blank)
        self.assertFalse(is_multiple)
        self.assertEqual(count, 0)
        detector.release()

    def test_draw_detections(self):
        """Test drawing detections on frame."""
        from vision.face_detector import FaceDetector
        detector = FaceDetector()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        faces_data = [{"bbox": (100, 100, 200, 200), "confidence": 0.95}]
        annotated = detector.draw_detections(frame, faces_data)
        self.assertEqual(annotated.shape, frame.shape)
        detector.release()


class TestFaceRecognizer(unittest.TestCase):
    """Test suite for FaceRecognizer — encoding and matching logic."""

    def test_initialization(self):
        """Test FaceRecognizer initializes."""
        from vision.face_recognizer import FaceRecognizer
        recognizer = FaceRecognizer(tolerance=0.5)
        self.assertIsNotNone(recognizer)
        self.assertEqual(recognizer.tolerance, 0.5)

    def test_generate_encoding_no_face(self):
        """Test encoding generation fails on blank image."""
        from vision.face_recognizer import FaceRecognizer
        recognizer = FaceRecognizer()
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        encoding, success, message = recognizer.generate_encoding(blank)
        self.assertFalse(success)
        self.assertIsNone(encoding)
        self.assertIn("No face", message)

    def test_save_and_load_encoding(self):
        """Test saving and loading a face encoding."""
        import tempfile
        from vision.face_recognizer import FaceRecognizer
        recognizer = FaceRecognizer()

        # Create a dummy encoding
        dummy_encoding = np.random.rand(128).astype(np.float64)

        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            temp_path = f.name

        try:
            # Save
            result = recognizer.save_encoding(dummy_encoding, temp_path)
            self.assertTrue(result)

            # Load
            loaded = recognizer.load_encoding(temp_path)
            self.assertIsNotNone(loaded)
            np.testing.assert_array_almost_equal(loaded, dummy_encoding)
        finally:
            os.unlink(temp_path)

    def test_load_nonexistent_encoding(self):
        """Test loading from nonexistent file returns None."""
        from vision.face_recognizer import FaceRecognizer
        recognizer = FaceRecognizer()
        result = recognizer.load_encoding("/nonexistent/path/encoding.pkl")
        self.assertIsNone(result)


class TestHeadPoseEstimator(unittest.TestCase):
    """Test suite for HeadPoseEstimator."""

    def test_initialization(self):
        """Test HeadPoseEstimator initializes."""
        from vision.head_pose import HeadPoseEstimator
        estimator = HeadPoseEstimator(yaw_threshold=30.0, pitch_threshold=25.0)
        self.assertIsNotNone(estimator)
        self.assertEqual(estimator.yaw_threshold, 30.0)
        estimator.release()

    def test_no_face_returns_none(self):
        """Test pose estimation returns None for blank image."""
        from vision.head_pose import HeadPoseEstimator
        estimator = HeadPoseEstimator()
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        result = estimator.estimate_pose(blank)
        self.assertIsNone(result)
        estimator.release()

    def test_normalize_angle(self):
        """Test angle normalization."""
        from vision.head_pose import HeadPoseEstimator
        estimator = HeadPoseEstimator()
        self.assertEqual(estimator._normalize_angle(0), 0)
        self.assertEqual(estimator._normalize_angle(360), 0)
        self.assertEqual(estimator._normalize_angle(-360), 0)
        self.assertAlmostEqual(estimator._normalize_angle(190), -170)
        estimator.release()

    def test_get_direction(self):
        """Test direction determination."""
        from vision.head_pose import HeadPoseEstimator
        estimator = HeadPoseEstimator(yaw_threshold=30, pitch_threshold=25)
        self.assertEqual(estimator._get_direction(0, 0), "center")
        self.assertIn("left", estimator._get_direction(-35, 0))
        self.assertIn("right", estimator._get_direction(35, 0))
        self.assertIn("up", estimator._get_direction(0, 30))
        self.assertIn("down", estimator._get_direction(0, -30))
        estimator.release()


class TestEyeGazeDetector(unittest.TestCase):
    """Test suite for EyeGazeDetector."""

    def test_initialization(self):
        """Test EyeGazeDetector initializes."""
        from vision.eye_gaze import EyeGazeDetector
        detector = EyeGazeDetector(gaze_threshold=0.25)
        self.assertIsNotNone(detector)
        self.assertEqual(detector.gaze_threshold, 0.25)
        detector.release()

    def test_no_face_returns_none(self):
        """Test gaze detection returns None for blank image."""
        from vision.eye_gaze import EyeGazeDetector
        detector = EyeGazeDetector()
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        result = detector.detect_gaze(blank)
        self.assertIsNone(result)
        detector.release()

    def test_gaze_direction(self):
        """Test gaze direction mapping."""
        from vision.eye_gaze import EyeGazeDetector
        detector = EyeGazeDetector(gaze_threshold=0.25)
        self.assertEqual(detector._get_gaze_direction(0.5), "center")
        self.assertEqual(detector._get_gaze_direction(0.1), "looking_left")
        self.assertEqual(detector._get_gaze_direction(0.9), "looking_right")
        detector.release()

    def test_reset_blink_counter(self):
        """Test blink counter reset."""
        from vision.eye_gaze import EyeGazeDetector
        detector = EyeGazeDetector()
        detector.total_blinks = 10
        detector.frame_count = 100
        detector.reset_blink_counter()
        self.assertEqual(detector.total_blinks, 0)
        self.assertEqual(detector.frame_count, 0)
        detector.release()


class TestPhoneDetector(unittest.TestCase):
    """Test suite for PhoneDetector."""

    def test_initialization_without_yolo(self):
        """Test PhoneDetector initializes without YOLO files."""
        from vision.phone_detector import PhoneDetector
        detector = PhoneDetector()
        self.assertIsNotNone(detector)
        self.assertFalse(detector.use_yolo)

    def test_heuristic_blank_image(self):
        """Test heuristic detection on blank image finds no phone."""
        from vision.phone_detector import PhoneDetector
        detector = PhoneDetector()
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        detected, confidence, bbox = detector.detect_phone(blank)
        self.assertFalse(detected)


class TestProctoringEngine(unittest.TestCase):
    """Test suite for ProctoringEngine."""

    def test_initialization(self):
        """Test ProctoringEngine initializes."""
        from vision.proctoring_engine import ProctoringEngine
        config = {
            "FACE_DETECTION_CONFIDENCE": 0.6,
            "FACE_RECOGNITION_TOLERANCE": 0.5,
            "HEAD_POSE_YAW_THRESHOLD": 30.0,
            "HEAD_POSE_PITCH_THRESHOLD": 25.0,
            "EYE_GAZE_THRESHOLD": 0.25,
            "BLUR_THRESHOLD": 80.0,
            "PHONE_DETECTION_CONFIDENCE": 0.45,
            "YOLO_CONFIG": None,
            "YOLO_WEIGHTS": None,
            "YOLO_CLASSES": None,
        }
        engine = ProctoringEngine(config)
        self.assertIsNotNone(engine)
        engine.release()

    def test_violation_types_defined(self):
        """Test that all violation types are defined."""
        from vision.proctoring_engine import ProctoringEngine
        expected_types = [
            "face_missing", "multiple_faces", "unknown_face",
            "face_blur", "head_pose", "eye_gaze", "phone_detected",
            "tab_switch", "fullscreen_exit", "copy_paste",
            "right_click", "keyboard_shortcut", "exam_terminated",
        ]
        for vtype in expected_types:
            self.assertIn(vtype, ProctoringEngine.VIOLATION_TYPES)

    def test_decode_invalid_frame(self):
        """Test decoding invalid base64 returns None."""
        from vision.proctoring_engine import ProctoringEngine
        config = {
            "FACE_DETECTION_CONFIDENCE": 0.6,
            "FACE_RECOGNITION_TOLERANCE": 0.5,
            "HEAD_POSE_YAW_THRESHOLD": 30.0,
            "HEAD_POSE_PITCH_THRESHOLD": 25.0,
            "EYE_GAZE_THRESHOLD": 0.25,
            "BLUR_THRESHOLD": 80.0,
            "PHONE_DETECTION_CONFIDENCE": 0.45,
            "YOLO_CONFIG": None,
            "YOLO_WEIGHTS": None,
            "YOLO_CLASSES": None,
        }
        engine = ProctoringEngine(config)
        result = engine._decode_frame("not_valid_base64!!!")
        self.assertIsNone(result)
        engine.release()

    def test_create_browser_violation(self):
        """Test creating a browser violation."""
        from vision.proctoring_engine import ProctoringEngine
        config = {
            "FACE_DETECTION_CONFIDENCE": 0.6,
            "FACE_RECOGNITION_TOLERANCE": 0.5,
            "HEAD_POSE_YAW_THRESHOLD": 30.0,
            "HEAD_POSE_PITCH_THRESHOLD": 25.0,
            "EYE_GAZE_THRESHOLD": 0.25,
            "BLUR_THRESHOLD": 80.0,
            "PHONE_DETECTION_CONFIDENCE": 0.45,
            "YOLO_CONFIG": None,
            "YOLO_WEIGHTS": None,
            "YOLO_CLASSES": None,
        }
        engine = ProctoringEngine(config)
        violation = engine.create_browser_violation("tab_switch", "Tab switched")
        self.assertIsNotNone(violation)
        self.assertEqual(violation["type"], "tab_switch")
        self.assertEqual(violation["confidence"], 1.0)
        engine.release()


if __name__ == "__main__":
    unittest.main()
