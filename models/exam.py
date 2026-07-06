"""
Exam, ExamQuestion, and ExamAnswer models.
"""

from datetime import datetime
from database.db import db


class Exam(db.Model):
    """Exam model representing an examination."""

    __tablename__ = "exams"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    duration_minutes = db.Column(db.Integer, nullable=False, default=30)
    total_marks = db.Column(db.Integer, nullable=False, default=0)
    passing_marks = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    questions = db.relationship("ExamQuestion", backref="exam", lazy="dynamic", cascade="all, delete-orphan")
    answers = db.relationship("ExamAnswer", backref="exam", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Exam {self.title}>"


class ExamQuestion(db.Model):
    """ExamQuestion model representing an MCQ question."""

    __tablename__ = "exam_questions"

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"), nullable=False)
    question_number = db.Column(db.Integer, nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(500), nullable=False)
    option_b = db.Column(db.String(500), nullable=False)
    option_c = db.Column(db.String(500), nullable=False)
    option_d = db.Column(db.String(500), nullable=False)
    correct_option = db.Column(db.String(1), nullable=False)  # A, B, C, or D
    marks = db.Column(db.Integer, nullable=False, default=2)

    def __repr__(self):
        return f"<ExamQuestion Q{self.question_number} — Exam {self.exam_id}>"


class ExamAnswer(db.Model):
    """ExamAnswer model representing a student's answer to a question."""

    __tablename__ = "exam_answers"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("exam_questions.id"), nullable=False)
    selected_option = db.Column(db.String(1), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    question = db.relationship("ExamQuestion", backref="answers")

    def __repr__(self):
        return f"<ExamAnswer Student {self.student_id} Q{self.question_id} = {self.selected_option}>"
