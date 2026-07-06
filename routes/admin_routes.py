"""
Admin routes for admin dashboard, student management, reports, and statistics.
"""

import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, current_app, jsonify

from utils.decorators import admin_login_required
from models.student import Student
from models.exam import Exam
from models.violation import Violation
from models.activity_log import ActivityLog
from models.report import Report
from database.db import db
from services.violation_service import ViolationService
from services.activity_service import ActivityService
from services.report_service import ReportService
from services.exam_service import ExamService

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@admin_login_required
def dashboard():
    """Admin dashboard with statistics overview."""
    total_students = Student.query.count()
    active_students = Student.query.filter_by(is_active=True).count()
    total_violations = Violation.query.count()
    total_reports = Report.query.count()
    total_exams = Exam.query.count()
    total_activities = ActivityLog.query.count()

    recent_activities = ActivityService.get_recent_activities(limit=15)
    violation_stats = ViolationService.get_violation_statistics()

    # Students with most violations
    top_violators = db.session.query(
        Student.full_name,
        Student.student_id,
        db.func.count(Violation.id).label("violation_count")
    ).join(Violation, Student.id == Violation.student_id
    ).group_by(Student.id
    ).order_by(db.func.count(Violation.id).desc()
    ).limit(5).all()

    return render_template(
        "admin/dashboard.html",
        total_students=total_students,
        active_students=active_students,
        total_violations=total_violations,
        total_reports=total_reports,
        total_exams=total_exams,
        total_activities=total_activities,
        recent_activities=recent_activities,
        violation_stats=violation_stats,
        top_violators=top_violators,
    )


@admin_bp.route("/students")
@admin_login_required
def students():
    """View and manage registered students."""
    search = request.args.get("search", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 15

    query = Student.query
    if search:
        query = query.filter(
            db.or_(
                Student.full_name.ilike(f"%{search}%"),
                Student.student_id.ilike(f"%{search}%"),
                Student.email.ilike(f"%{search}%"),
                Student.department.ilike(f"%{search}%"),
            )
        )

    pagination = query.order_by(Student.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template(
        "admin/students.html",
        students=pagination.items,
        pagination=pagination,
        search=search,
    )


@admin_bp.route("/students/delete/<int:student_id>", methods=["POST"])
@admin_login_required
def delete_student(student_id):
    """Delete a student and associated data."""
    student = Student.query.get(student_id)
    if not student:
        flash("Student not found.", "danger")
        return redirect(url_for("admin.students"))

    # Delete associated files
    if student.face_image_path and os.path.exists(student.face_image_path):
        os.remove(student.face_image_path)
    if student.face_encoding_path and os.path.exists(student.face_encoding_path):
        os.remove(student.face_encoding_path)

    student_name = student.full_name
    db.session.delete(student)
    db.session.commit()

    flash(f"Student '{student_name}' has been deleted.", "success")
    return redirect(url_for("admin.students"))


@admin_bp.route("/violations")
@admin_login_required
def violations():
    """View all violations."""
    page = request.args.get("page", 1, type=int)
    per_page = 20
    filter_type = request.args.get("type", "").strip()

    query = Violation.query
    if filter_type:
        query = query.filter_by(violation_type=filter_type)

    pagination = query.order_by(Violation.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    violation_types = db.session.query(Violation.violation_type).distinct().all()
    violation_types = [v[0] for v in violation_types]

    return render_template(
        "admin/violations.html",
        violations=pagination.items,
        pagination=pagination,
        violation_types=violation_types,
        current_filter=filter_type,
    )


@admin_bp.route("/activity-logs")
@admin_login_required
def activity_logs():
    """View activity logs."""
    page = request.args.get("page", 1, type=int)
    per_page = 25
    filter_type = request.args.get("type", "").strip()

    query = ActivityLog.query
    if filter_type:
        query = query.filter_by(activity_type=filter_type)

    pagination = query.order_by(ActivityLog.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    activity_types = db.session.query(ActivityLog.activity_type).distinct().all()
    activity_types = [a[0] for a in activity_types]

    return render_template(
        "admin/activity_logs.html",
        logs=pagination.items,
        pagination=pagination,
        activity_types=activity_types,
        current_filter=filter_type,
    )


@admin_bp.route("/reports")
@admin_login_required
def reports():
    """View all generated reports."""
    reports_list = ReportService.get_all_reports(limit=100)
    return render_template("admin/reports.html", reports=reports_list)


@admin_bp.route("/reports/download/<int:report_id>")
@admin_login_required
def download_report(report_id):
    """Download a report PDF."""
    report = ReportService.get_report_by_id(report_id)
    if not report or not os.path.exists(report.report_path):
        flash("Report not found.", "danger")
        return redirect(url_for("admin.reports"))

    return send_file(report.report_path, as_attachment=True)


@admin_bp.route("/reports/generate/<int:student_id>/<int:exam_id>", methods=["POST"])
@admin_login_required
def generate_report(student_id, exam_id):
    """Generate a report for a student exam."""
    filepath, success, message = ReportService.generate_report(
        student_id, exam_id, current_app.config["REPORTS_FOLDER"]
    )

    if success:
        flash("Report generated successfully.", "success")
    else:
        flash(f"Report generation failed: {message}", "danger")

    return redirect(url_for("admin.reports"))


@admin_bp.route("/statistics")
@admin_login_required
def statistics():
    """Statistics dashboard with charts."""
    total_students = Student.query.count()
    total_violations = Violation.query.count()
    total_reports = Report.query.count()

    violation_stats = ViolationService.get_violation_statistics()

    # Violations by day (last 7 days)
    from datetime import datetime, timedelta
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    daily_violations = db.session.query(
        db.func.date(Violation.timestamp).label("date"),
        db.func.count(Violation.id).label("count"),
    ).filter(Violation.timestamp >= seven_days_ago
    ).group_by(db.func.date(Violation.timestamp)
    ).order_by(db.func.date(Violation.timestamp)).all()

    # Students per department
    dept_counts = db.session.query(
        Student.department,
        db.func.count(Student.id),
    ).group_by(Student.department).all()

    # Exam pass/fail rates
    pass_count = Report.query.filter_by(is_passed=True).count()
    fail_count = Report.query.filter_by(is_passed=False).count()

    return render_template(
        "admin/statistics.html",
        total_students=total_students,
        total_violations=total_violations,
        total_reports=total_reports,
        violation_stats=violation_stats,
        daily_violations=[(str(d.date), d.count) for d in daily_violations],
        dept_counts=[(d or "Unknown", c) for d, c in dept_counts],
        pass_count=pass_count,
        fail_count=fail_count,
    )


@admin_bp.route("/api/stats")
@admin_login_required
def api_stats():
    """API endpoint for dashboard statistics (for AJAX charts)."""
    violation_stats = ViolationService.get_violation_statistics()
    return jsonify({
        "violation_by_type": violation_stats["by_type"],
        "violation_by_severity": violation_stats["by_severity"],
        "total": violation_stats["total"],
    })
