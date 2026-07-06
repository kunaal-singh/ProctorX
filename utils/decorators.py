"""
Decorators for authentication and authorization.
"""

from functools import wraps
from flask import session, redirect, url_for, flash, request


def student_login_required(f):
    """Decorator to require student login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "student_id" not in session:
            flash("Please login to access this page.", "warning")
            return redirect(url_for("auth.student_login"))
        return f(*args, **kwargs)
    return decorated_function


def admin_login_required(f):
    """Decorator to require admin login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_id" not in session:
            flash("Please login as admin to access this page.", "warning")
            return redirect(url_for("auth.admin_login"))
        return f(*args, **kwargs)
    return decorated_function


def face_registered_required(f):
    """Decorator to require face registration before proceeding."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from models.student import Student
        student = Student.query.get(session.get("student_id"))
        if not student or not student.is_face_registered:
            flash("Please register your face before proceeding.", "warning")
            return redirect(url_for("student.face_capture"))
        return f(*args, **kwargs)
    return decorated_function
