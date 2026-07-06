"""
Violation model for tracking proctoring violations.
"""

from datetime import datetime
from database.db import db


class Violation(db.Model):
    """Violation model representing a detected proctoring violation."""

    __tablename__ = "violations"

    # Severity levels
    SEVERITY_LOW = "low"
    SEVERITY_MEDIUM = "medium"
    SEVERITY_HIGH = "high"
    SEVERITY_CRITICAL = "critical"

    # Violation type to severity mapping
    SEVERITY_MAP = {
        "face_missing": "medium",
        "multiple_faces": "high",
        "unknown_face": "high",
        "face_blur": "low",
        "head_pose": "medium",
        "eye_gaze": "medium",
        "phone_detected": "high",
        "tab_switch": "medium",
        "fullscreen_exit": "medium",
        "copy_paste": "medium",
        "right_click": "low",
        "keyboard_shortcut": "medium",
        "exam_terminated": "critical",
    }

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"), nullable=True)
    violation_type = db.Column(db.String(50), nullable=False, index=True)
    description = db.Column(db.Text)
    confidence_score = db.Column(db.Float, default=0.0)
    severity = db.Column(db.String(20), default="medium")
    warning_number = db.Column(db.Integer, default=0)
    screenshot_path = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<Violation {self.violation_type} — Student {self.student_id}>"

    @staticmethod
    def get_severity(violation_type):
        """Get severity level for a violation type."""
        return Violation.SEVERITY_MAP.get(violation_type, "medium")
