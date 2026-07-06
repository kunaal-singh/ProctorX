"""
Tests for authentication services and routes.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from database.db import db
from models.student import Student
from models.admin import Admin
from services.auth_service import AuthService


class TestAuthService(unittest.TestCase):
    """Test suite for AuthService."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

    def tearDown(self):
        """Tear down test fixtures."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_register_student_success(self):
        """Test successful student registration."""
        student, success, message = AuthService.register_student(
            full_name="John Doe",
            email="john@test.com",
            password="password123",
            phone="1234567890",
            department="Computer Science",
            semester="4th",
        )
        self.assertTrue(success)
        self.assertIsNotNone(student)
        self.assertEqual(student.full_name, "John Doe")
        self.assertEqual(student.email, "john@test.com")
        self.assertTrue(student.student_id.startswith("STU"))

    def test_register_student_duplicate_email(self):
        """Test registration with duplicate email fails."""
        AuthService.register_student("John Doe", "john@test.com", "pass123")
        student, success, message = AuthService.register_student(
            "Jane Doe", "john@test.com", "pass456"
        )
        self.assertFalse(success)
        self.assertIsNone(student)
        self.assertIn("already registered", message)

    def test_login_student_success(self):
        """Test successful student login."""
        AuthService.register_student("John Doe", "john@test.com", "password123")
        student, success, message = AuthService.login_student("john@test.com", "password123")
        self.assertTrue(success)
        self.assertIsNotNone(student)
        self.assertEqual(student.email, "john@test.com")

    def test_login_student_wrong_password(self):
        """Test login with wrong password fails."""
        AuthService.register_student("John Doe", "john@test.com", "password123")
        student, success, message = AuthService.login_student("john@test.com", "wrongpass")
        self.assertFalse(success)
        self.assertIsNone(student)

    def test_login_student_nonexistent(self):
        """Test login with nonexistent email fails."""
        student, success, message = AuthService.login_student("nobody@test.com", "pass")
        self.assertFalse(success)
        self.assertIsNone(student)

    def test_login_admin_success(self):
        """Test successful admin login (seeded admin)."""
        admin, success, message = AuthService.login_admin("admin", "admin123")
        self.assertTrue(success)
        self.assertIsNotNone(admin)
        self.assertEqual(admin.username, "admin")

    def test_login_admin_wrong_password(self):
        """Test admin login with wrong password fails."""
        admin, success, message = AuthService.login_admin("admin", "wrongpass")
        self.assertFalse(success)
        self.assertIsNone(admin)

    def test_change_password(self):
        """Test password change."""
        student, _, _ = AuthService.register_student("John Doe", "john@test.com", "oldpass")
        success, message = AuthService.change_password(student.id, "oldpass", "newpass")
        self.assertTrue(success)

        # Verify new password works
        student, success, _ = AuthService.login_student("john@test.com", "newpass")
        self.assertTrue(success)

    def test_change_password_wrong_current(self):
        """Test password change with wrong current password."""
        student, _, _ = AuthService.register_student("John Doe", "john@test.com", "oldpass")
        success, message = AuthService.change_password(student.id, "wrongold", "newpass")
        self.assertFalse(success)


class TestAuthRoutes(unittest.TestCase):
    """Test suite for authentication routes."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

    def tearDown(self):
        """Tear down test fixtures."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_index_page(self):
        """Test landing page loads."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"AI", response.data)

    def test_student_login_page(self):
        """Test student login page loads."""
        response = self.client.get("/student/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Student Login", response.data)

    def test_student_register_page(self):
        """Test student registration page loads."""
        response = self.client.get("/student/register")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Registration", response.data)

    def test_admin_login_page(self):
        """Test admin login page loads."""
        response = self.client.get("/admin/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Admin Login", response.data)

    def test_student_register_post(self):
        """Test student registration POST."""
        response = self.client.post("/student/register", data={
            "full_name": "Test Student",
            "email": "test@student.com",
            "password": "testpass123",
            "confirm_password": "testpass123",
            "phone": "9876543210",
            "department": "Computer Science",
            "semester": "4th",
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        student = Student.query.filter_by(email="test@student.com").first()
        self.assertIsNotNone(student)

    def test_student_login_post(self):
        """Test student login POST."""
        AuthService.register_student("Test Student", "test@student.com", "testpass123")
        response = self.client.post("/student/login", data={
            "email": "test@student.com",
            "password": "testpass123",
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_admin_login_post(self):
        """Test admin login POST."""
        response = self.client.post("/admin/login", data={
            "username": "admin",
            "password": "admin123",
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_student_dashboard_requires_login(self):
        """Test student dashboard redirects without login."""
        response = self.client.get("/student/dashboard", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"login", response.data.lower())

    def test_admin_dashboard_requires_login(self):
        """Test admin dashboard redirects without login."""
        response = self.client.get("/admin/dashboard", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"login", response.data.lower())

    def test_student_logout(self):
        """Test student logout clears session."""
        AuthService.register_student("Test Student", "test@student.com", "testpass123")
        self.client.post("/student/login", data={
            "email": "test@student.com",
            "password": "testpass123",
        })
        response = self.client.get("/student/logout", follow_redirects=True)
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
