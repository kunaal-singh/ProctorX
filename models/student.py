"""
Student model for the proctoring system.
"""

from datetime import datetime
from database.db import db


class Student(db.Model):
    """Student model representing registered exam takers."""

    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    phone = db.Column(db.String(20))
    department = db.Column(db.String(100))
    semester = db.Column(db.String(20))
    face_image_path = db.Column(db.String(500))
    face_encoding_path = db.Column(db.String(500))
    is_face_registered = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    violations = db.relationship("Violation", backref="student", lazy="dynamic", cascade="all, delete-orphan")
    activity_logs = db.relationship("ActivityLog", backref="student_ref", lazy="dynamic", cascade="all, delete-orphan")
    reports = db.relationship("Report", backref="student", lazy="dynamic", cascade="all, delete-orphan")
    exam_answers = db.relationship("ExamAnswer", backref="student", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Student {self.student_id} — {self.full_name}>"
