"""
Application configuration module.
Contains settings for development, testing, and production environments.
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "proctor-ai-secret-key-2026-ultra-secure")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'database', 'proctoring.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload directories
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    ENCODINGS_FOLDER = os.path.join(BASE_DIR, "encodings")
    SCREENSHOTS_FOLDER = os.path.join(BASE_DIR, "screenshots")
    REPORTS_FOLDER = os.path.join(BASE_DIR, "reports")
    LOGS_FOLDER = os.path.join(BASE_DIR, "logs")

    # File upload limits
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # Face Recognition Settings
    FACE_RECOGNITION_TOLERANCE = 0.5
    FACE_DETECTION_CONFIDENCE = 0.6

    # Head Pose Thresholds
    HEAD_POSE_YAW_THRESHOLD = 30.0
    HEAD_POSE_PITCH_THRESHOLD = 25.0

    # Eye Gaze Threshold
    EYE_GAZE_THRESHOLD = 0.25

    # Blur Detection
    BLUR_THRESHOLD = 80.0

    # Phone Detection
    PHONE_DETECTION_CONFIDENCE = 0.45
    YOLO_CONFIG = os.path.join(BASE_DIR, "vision", "yolov3-tiny.cfg")
    YOLO_WEIGHTS = os.path.join(BASE_DIR, "vision", "yolov3-tiny.weights")
    YOLO_CLASSES = os.path.join(BASE_DIR, "vision", "coco.names")

    # Exam Settings
    MAX_WARNINGS = 15
    EXAM_DURATION_MINUTES = 30

    @staticmethod
    def init_app(app):
        """Initialize application directories."""
        dirs = [
            app.config.get("UPLOAD_FOLDER", "uploads"),
            app.config.get("ENCODINGS_FOLDER", "encodings"),
            app.config.get("SCREENSHOTS_FOLDER", "screenshots"),
            app.config.get("REPORTS_FOLDER", "reports"),
            app.config.get("LOGS_FOLDER", "logs"),
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
