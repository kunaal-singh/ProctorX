"""
Authentication routes for student and admin login/logout/registration.
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from services.auth_service import AuthService
from services.activity_service import ActivityService
from models.activity_log import ActivityLog
from models.admin import Admin
from database.db import db

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    """Landing page."""
    return render_template("index.html")


@auth_bp.route("/student/login", methods=["GET", "POST"])
def student_login():
    """Student login page."""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please provide both email and password.", "danger")
            return render_template("student/login.html")

        student, success, message = AuthService.login_student(email, password)
        if success:
            session["student_id"] = student.id
            session["student_name"] = student.full_name
            session["student_sid"] = student.student_id
            session["is_face_registered"] = student.is_face_registered

            ActivityService.log_activity(
                student.id, ActivityLog.LOGIN,
                f"Student {student.full_name} logged in."
            )

            flash(message, "success")
            return redirect(url_for("student.dashboard"))
        else:
            flash(message, "danger")

    return render_template("student/login.html")


@auth_bp.route("/student/register", methods=["GET", "POST"])
def student_register():
    """Student registration page."""
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        phone = request.form.get("phone", "").strip()
        department = request.form.get("department", "").strip()
        semester = request.form.get("semester", "").strip()

        # Validation
        if not full_name or not email or not password:
            flash("Please fill in all required fields.", "danger")
            return render_template("student/register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("student/register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("student/register.html")

        student, success, message = AuthService.register_student(
            full_name, email, password, phone, department, semester
        )

        if success:
            ActivityService.log_activity(
                student.id, ActivityLog.REGISTER,
                f"Student {full_name} registered."
            )
            flash(f"Registration successful! Your Student ID is {student.student_id}", "success")
            return redirect(url_for("auth.student_login"))
        else:
            flash(message, "danger")

    return render_template("student/register.html")


@auth_bp.route("/student/logout")
def student_logout():
    """Student logout."""
    student_id = session.get("student_id")
    if student_id:
        ActivityService.log_activity(
            student_id, ActivityLog.LOGOUT,
            "Student logged out."
        )
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.student_login"))


@auth_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Admin login page."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Please provide both username and password.", "danger")
            return render_template("admin/login.html")

        admin, success, message = AuthService.login_admin(username, password)
        if success:
            session["admin_id"] = admin.id
            session["admin_name"] = admin.full_name
            admin.last_login = datetime.utcnow()
            db.session.commit()

            flash(message, "success")
            return redirect(url_for("admin.dashboard"))
        else:
            flash(message, "danger")

    return render_template("admin/login.html")


@auth_bp.route("/admin/logout")
def admin_logout():
    """Admin logout."""
    session.clear()
    flash("Admin logged out.", "info")
    return redirect(url_for("auth.admin_login"))
