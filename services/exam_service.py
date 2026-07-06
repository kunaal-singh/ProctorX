"""
Exam service for managing exams, questions, and student answers.
"""

from datetime import datetime
from database.db import db
from models.exam import Exam, ExamQuestion, ExamAnswer
from models.student import Student


class ExamService:
    """Service for exam operations."""

    @staticmethod
    def get_active_exams():
        """Get all active exams.

        Returns:
            List of active Exam objects.
        """
        return Exam.query.filter_by(is_active=True).all()

    @staticmethod
    def get_exam_by_id(exam_id):
        """Get exam by ID.

        Args:
            exam_id: Exam database ID.

        Returns:
            Exam object or None.
        """
        return Exam.query.get(exam_id)

    @staticmethod
    def get_exam_questions(exam_id):
        """Get all questions for an exam.

        Args:
            exam_id: Exam database ID.

        Returns:
            List of ExamQuestion objects ordered by question number.
        """
        return ExamQuestion.query.filter_by(exam_id=exam_id).order_by(
            ExamQuestion.question_number
        ).all()

    @staticmethod
    def save_answer(student_id, exam_id, question_id, selected_option):
        """Save or update a student's answer.

        Args:
            student_id: Student database ID.
            exam_id: Exam database ID.
            question_id: Question database ID.
            selected_option: Selected option (A, B, C, or D).

        Returns:
            Tuple of (success, message).
        """
        try:
            # Check if answer already exists
            existing = ExamAnswer.query.filter_by(
                student_id=student_id,
                exam_id=exam_id,
                question_id=question_id,
            ).first()

            question = ExamQuestion.query.get(question_id)
            if not question:
                return False, "Question not found."

            is_correct = selected_option.upper() == question.correct_option.upper()
            marks = question.marks if is_correct else 0

            if existing:
                existing.selected_option = selected_option.upper()
                existing.is_correct = is_correct
                existing.marks_obtained = marks
                existing.answered_at = datetime.utcnow()
            else:
                answer = ExamAnswer(
                    student_id=student_id,
                    exam_id=exam_id,
                    question_id=question_id,
                    selected_option=selected_option.upper(),
                    is_correct=is_correct,
                    marks_obtained=marks,
                )
                db.session.add(answer)

            db.session.commit()
            return True, "Answer saved."
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def submit_exam(student_id, exam_id):
        """Submit the exam and calculate score.

        Args:
            student_id: Student database ID.
            exam_id: Exam database ID.

        Returns:
            Dictionary with exam results.
        """
        exam = Exam.query.get(exam_id)
        if not exam:
            return {"success": False, "message": "Exam not found."}

        answers = ExamAnswer.query.filter_by(
            student_id=student_id,
            exam_id=exam_id,
        ).all()

        total_score = sum(a.marks_obtained for a in answers)
        total_questions = exam.questions.count()
        answered_count = len(answers)
        correct_count = sum(1 for a in answers if a.is_correct)

        return {
            "success": True,
            "exam_id": exam_id,
            "student_id": student_id,
            "total_score": total_score,
            "total_marks": exam.total_marks,
            "passing_marks": exam.passing_marks,
            "is_passed": total_score >= exam.passing_marks,
            "total_questions": total_questions,
            "answered_count": answered_count,
            "correct_count": correct_count,
            "percentage": round((total_score / exam.total_marks) * 100, 1) if exam.total_marks > 0 else 0,
        }

    @staticmethod
    def get_student_answers(student_id, exam_id):
        """Get all answers for a student in an exam.

        Args:
            student_id: Student database ID.
            exam_id: Exam database ID.

        Returns:
            List of ExamAnswer objects.
        """
        return ExamAnswer.query.filter_by(
            student_id=student_id,
            exam_id=exam_id,
        ).all()

    @staticmethod
    def has_student_taken_exam(student_id, exam_id):
        """Check if a student has already submitted an exam.

        Args:
            student_id: Student database ID.
            exam_id: Exam database ID.

        Returns:
            Boolean.
        """
        count = ExamAnswer.query.filter_by(
            student_id=student_id,
            exam_id=exam_id,
        ).count()
        return count > 0
