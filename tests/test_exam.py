"""
Tests for exam services — questions, answers, scoring, and violations.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from database.db import db
from models.student import Student
from models.exam import Exam, ExamQuestion, ExamAnswer
from models.violation import Violation
from services.auth_service import AuthService
from services.exam_service import ExamService
from services.violation_service import ViolationService
from services.activity_service import ActivityService
from models.activity_log import ActivityLog


class TestExamService(unittest.TestCase):
    """Test suite for ExamService."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

        # Register a test student
        self.student, _, _ = AuthService.register_student(
            "Test Student", "test@exam.com", "password123"
        )

    def tearDown(self):
        """Tear down test fixtures."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_get_active_exams(self):
        """Test retrieving active exams."""
        exams = ExamService.get_active_exams()
        self.assertIsInstance(exams, list)
        # Seeded exam should exist
        self.assertGreater(len(exams), 0)

    def test_get_exam_by_id(self):
        """Test retrieving exam by ID."""
        exams = ExamService.get_active_exams()
        if exams:
            exam = ExamService.get_exam_by_id(exams[0].id)
            self.assertIsNotNone(exam)
            self.assertEqual(exam.title, "General Knowledge Assessment")

    def test_get_exam_questions(self):
        """Test retrieving exam questions."""
        exams = ExamService.get_active_exams()
        if exams:
            questions = ExamService.get_exam_questions(exams[0].id)
            self.assertIsInstance(questions, list)
            self.assertEqual(len(questions), 20)

    def test_save_answer(self):
        """Test saving a student answer."""
        exams = ExamService.get_active_exams()
        if exams:
            questions = ExamService.get_exam_questions(exams[0].id)
            if questions:
                success, message = ExamService.save_answer(
                    self.student.id, exams[0].id, questions[0].id, "B"
                )
                self.assertTrue(success)

    def test_save_answer_updates_existing(self):
        """Test that saving answer again updates instead of duplicating."""
        exams = ExamService.get_active_exams()
        if exams:
            questions = ExamService.get_exam_questions(exams[0].id)
            if questions:
                ExamService.save_answer(self.student.id, exams[0].id, questions[0].id, "A")
                ExamService.save_answer(self.student.id, exams[0].id, questions[0].id, "B")
                answers = ExamService.get_student_answers(self.student.id, exams[0].id)
                # Should only have one answer for this question
                q_answers = [a for a in answers if a.question_id == questions[0].id]
                self.assertEqual(len(q_answers), 1)
                self.assertEqual(q_answers[0].selected_option, "B")

    def test_submit_exam(self):
        """Test exam submission and scoring."""
        exams = ExamService.get_active_exams()
        if exams:
            questions = ExamService.get_exam_questions(exams[0].id)
            # Answer all questions with correct option
            for q in questions:
                ExamService.save_answer(
                    self.student.id, exams[0].id, q.id, q.correct_option
                )

            result = ExamService.submit_exam(self.student.id, exams[0].id)
            self.assertTrue(result["success"])
            self.assertEqual(result["total_score"], exams[0].total_marks)
            self.assertTrue(result["is_passed"])
            self.assertEqual(result["percentage"], 100.0)

    def test_submit_exam_partial(self):
        """Test partial exam submission."""
        exams = ExamService.get_active_exams()
        if exams:
            questions = ExamService.get_exam_questions(exams[0].id)
            # Answer only first question correctly
            if questions:
                ExamService.save_answer(
                    self.student.id, exams[0].id, questions[0].id,
                    questions[0].correct_option
                )

            result = ExamService.submit_exam(self.student.id, exams[0].id)
            self.assertTrue(result["success"])
            self.assertEqual(result["answered_count"], 1)
            self.assertEqual(result["correct_count"], 1)

    def test_has_student_taken_exam(self):
        """Test checking if student has taken exam."""
        exams = ExamService.get_active_exams()
        if exams:
            self.assertFalse(
                ExamService.has_student_taken_exam(self.student.id, exams[0].id)
            )
            questions = ExamService.get_exam_questions(exams[0].id)
            if questions:
                ExamService.save_answer(
                    self.student.id, exams[0].id, questions[0].id, "A"
                )
            self.assertTrue(
                ExamService.has_student_taken_exam(self.student.id, exams[0].id)
            )


class TestViolationService(unittest.TestCase):
    """Test suite for ViolationService."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

        self.student, _, _ = AuthService.register_student(
            "Test Student", "test@violation.com", "password123"
        )
        self.exam = ExamService.get_active_exams()[0]

    def tearDown(self):
        """Tear down test fixtures."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_record_violation(self):
        """Test recording a violation."""
        violation, success, message = ViolationService.record_violation(
            student_id=self.student.id,
            exam_id=self.exam.id,
            violation_type="face_missing",
            description="No face detected",
            confidence_score=0.95,
            warning_number=1,
        )
        self.assertTrue(success)
        self.assertIsNotNone(violation)
        self.assertEqual(violation.violation_type, "face_missing")
        self.assertEqual(violation.severity, "medium")

    def test_violation_count(self):
        """Test getting violation count."""
        for i in range(5):
            ViolationService.record_violation(
                self.student.id, self.exam.id,
                "face_missing", f"Warning {i+1}",
                0.9, warning_number=i+1,
            )
        count = ViolationService.get_violation_count(self.student.id, self.exam.id)
        self.assertEqual(count, 5)

    def test_get_student_violations(self):
        """Test retrieving student violations."""
        ViolationService.record_violation(
            self.student.id, self.exam.id,
            "multiple_faces", "2 faces detected", 0.85,
        )
        violations = ViolationService.get_student_violations(self.student.id)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].violation_type, "multiple_faces")

    def test_violation_severity(self):
        """Test violation severity assignment."""
        self.assertEqual(Violation.get_severity("unknown_face"), "high")
        self.assertEqual(Violation.get_severity("phone_detected"), "high")
        self.assertEqual(Violation.get_severity("face_blur"), "low")
        self.assertEqual(Violation.get_severity("head_pose"), "medium")
        self.assertEqual(Violation.get_severity("exam_terminated"), "critical")

    def test_violation_statistics(self):
        """Test violation statistics."""
        ViolationService.record_violation(
            self.student.id, self.exam.id, "face_missing", "", 0.9
        )
        ViolationService.record_violation(
            self.student.id, self.exam.id, "face_missing", "", 0.9
        )
        ViolationService.record_violation(
            self.student.id, self.exam.id, "phone_detected", "", 0.8
        )

        stats = ViolationService.get_violation_statistics()
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["by_type"]["face_missing"], 2)
        self.assertEqual(stats["by_type"]["phone_detected"], 1)

    def test_delete_student_violations(self):
        """Test deleting student violations."""
        ViolationService.record_violation(
            self.student.id, self.exam.id, "face_missing", "", 0.9
        )
        ViolationService.record_violation(
            self.student.id, self.exam.id, "tab_switch", "", 1.0
        )
        deleted = ViolationService.delete_student_violations(self.student.id)
        self.assertEqual(deleted, 2)
        self.assertEqual(
            ViolationService.get_violation_count(self.student.id, self.exam.id), 0
        )


class TestActivityService(unittest.TestCase):
    """Test suite for ActivityService."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

        self.student, _, _ = AuthService.register_student(
            "Test Student", "test@activity.com", "password123"
        )

    def tearDown(self):
        """Tear down test fixtures."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_log_activity(self):
        """Test logging an activity."""
        with self.app.test_request_context():
            log = ActivityService.log_activity(
                self.student.id, ActivityLog.LOGIN, "Student logged in."
            )
            self.assertIsNotNone(log)
            self.assertEqual(log.activity_type, ActivityLog.LOGIN)

    def test_get_student_activities(self):
        """Test retrieving student activities."""
        with self.app.test_request_context():
            ActivityService.log_activity(self.student.id, ActivityLog.LOGIN, "Login")
            ActivityService.log_activity(self.student.id, ActivityLog.EXAM_START, "Exam started")

            activities = ActivityService.get_student_activities(self.student.id)
            self.assertEqual(len(activities), 2)

    def test_activity_count(self):
        """Test total activity count."""
        with self.app.test_request_context():
            ActivityService.log_activity(self.student.id, ActivityLog.LOGIN, "Login")
            # Seeding also creates activities, so check it's at least 1
            count = ActivityService.get_activity_count()
            self.assertGreaterEqual(count, 1)


if __name__ == "__main__":
    unittest.main()
