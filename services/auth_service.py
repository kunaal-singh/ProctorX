"""
Authentication service for student and admin login, registration, and password management.
"""

from werkzeug.security import generate_password_hash, check_password_hash
from database.db import db
from models.student import Student
from models.admin import Admin
from utils.helpers import generate_student_id


class AuthService:
    """Authentication service handling user registration and login."""

    @staticmethod
    def register_student(full_name, email, password, phone=None, department=None, semester=None):
        """Register a new student.

        Args:
            full_name: Student full name.
            email: Student email.
            password: Plain text password.
            phone: Optional phone number.
            department: Optional department.
            semester: Optional semester.

        Returns:
            Tuple of (student, success, message).
        """
        # Check for existing email
        if Student.query.filter_by(email=email).first():
            return None, False, "Email already registered."

        student_id = generate_student_id()

        # Ensure unique student_id
        while Student.query.filter_by(student_id=student_id).first():
            student_id = generate_student_id()

        student = Student(
            student_id=student_id,
            full_name=full_name,
            email=email,
            password_hash=generate_password_hash(password),
            phone=phone,
            department=department,
            semester=semester,
        )

        try:
            db.session.add(student)
            db.session.commit()
            return student, True, "Registration successful."
        except Exception as e:
            db.session.rollback()
            return None, False, f"Registration failed: {str(e)}"

    @staticmethod
    def login_student(email, password):
        """Authenticate a student.

        Args:
            email: Student email.
            password: Plain text password.

        Returns:
            Tuple of (student, success, message).
        """
        student = Student.query.filter_by(email=email).first()
        if not student:
            return None, False, "Invalid email or password."

        if not student.is_active:
            return None, False, "Your account has been deactivated."

        if not check_password_hash(student.password_hash, password):
            return None, False, "Invalid email or password."

        return student, True, "Login successful."

    @staticmethod
    def login_admin(username, password):
        """Authenticate an admin.

        Args:
            username: Admin username.
            password: Plain text password.

        Returns:
            Tuple of (admin, success, message).
        """
        admin = Admin.query.filter_by(username=username).first()
        if not admin:
            return None, False, "Invalid username or password."

        if not admin.is_active:
            return None, False, "Admin account is deactivated."

        if not check_password_hash(admin.password_hash, password):
            return None, False, "Invalid username or password."

        return admin, True, "Login successful."

    @staticmethod
    def change_password(student_id, old_password, new_password):
        """Change a student's password.

        Args:
            student_id: Student database ID.
            old_password: Current password.
            new_password: New password.

        Returns:
            Tuple of (success, message).
        """
        student = Student.query.get(student_id)
        if not student:
            return False, "Student not found."

        if not check_password_hash(student.password_hash, old_password):
            return False, "Current password is incorrect."

        student.password_hash = generate_password_hash(new_password)
        db.session.commit()
        return True, "Password changed successfully."
