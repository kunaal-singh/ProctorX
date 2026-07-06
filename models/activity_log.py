"""
Activity log model for tracking user actions.
"""

from datetime import datetime
from database.db import db


class ActivityLog(db.Model):
    """Activity log for tracking all user actions in the system."""

    __tablename__ = "activity_logs"

    # Activity type constants
    LOGIN = "login"
    LOGOUT = "logout"
    REGISTRATION = "registration"
    FACE_CAPTURE = "face_capture"
    FACE_VERIFY = "face_verify"
    EXAM_START = "exam_start"
    EXAM_END = "exam_end"
    EXAM_SUBMIT = "exam_submit"
    EXAM_TERMINATED = "exam_terminated"
    VIOLATION = "violation"
    WARNING = "warning"
    REPORT_GENERATED = "report_generated"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=True)
    activity_type = db.Column(db.String(50), nullable=False, index=True)
    description = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(300))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<ActivityLog {self.activity_type} — {self.timestamp}>"
