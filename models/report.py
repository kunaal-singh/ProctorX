"""
Report model for storing generated proctoring reports.
"""

from datetime import datetime
from database.db import db


class Report(db.Model):
    """Report model representing a generated proctoring report."""

    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"), nullable=True)
    report_path = db.Column(db.String(500), nullable=False)
    total_violations = db.Column(db.Integer, default=0)
    total_warnings = db.Column(db.Integer, default=0)
    exam_score = db.Column(db.Integer, default=0)
    total_marks = db.Column(db.Integer, default=0)
    exam_status = db.Column(db.String(50), default="completed")
    is_passed = db.Column(db.Boolean, default=False)
    exam_start_time = db.Column(db.DateTime)
    exam_end_time = db.Column(db.DateTime)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Report Student {self.student_id} — Exam {self.exam_id}>"
