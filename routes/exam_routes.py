"""
Exam-related API routes for proctoring, answer submission, and violation reporting.
"""

import os
import pickle
from flask import Blueprint, request, session, current_app, jsonify

from utils.decorators import student_login_required
from services.exam_service import ExamService
from services.violation_service import ViolationService
from services.activity_service import ActivityService
from services.report_service import ReportService
from models.student import Student
from models.activity_log import ActivityLog
from vision.proctoring_engine import ProctoringEngine

exam_bp = Blueprint("exam_api", __name__, url_prefix="/api/exam")

# Global proctoring engine instance (lazy init)
_proctoring_engine = None


def _get_engine():
    """Get or create the proctoring engine singleton."""
    global _proctoring_engine
    if _proctoring_engine is None:
        config = {
            "FACE_DETECTION_CONFIDENCE": current_app.config.get("FACE_DETECTION_CONFIDENCE", 0.6),
            "FACE_RECOGNITION_TOLERANCE": current_app.config.get("FACE_RECOGNITION_TOLERANCE", 0.5),
            "HEAD_POSE_YAW_THRESHOLD": current_app.config.get("HEAD_POSE_YAW_THRESHOLD", 30.0),
            "HEAD_POSE_PITCH_THRESHOLD": current_app.config.get("HEAD_POSE_PITCH_THRESHOLD", 25.0),
            "EYE_GAZE_THRESHOLD": current_app.config.get("EYE_GAZE_THRESHOLD", 0.25),
            "BLUR_THRESHOLD": current_app.config.get("BLUR_THRESHOLD", 80.0),
            "PHONE_DETECTION_CONFIDENCE": current_app.config.get("PHONE_DETECTION_CONFIDENCE", 0.45),
            "YOLO_CONFIG": current_app.config.get("YOLO_CONFIG"),
            "YOLO_WEIGHTS": current_app.config.get("YOLO_WEIGHTS"),
            "YOLO_CLASSES": current_app.config.get("YOLO_CLASSES"),
        }
        _proctoring_engine = ProctoringEngine(config)
    return _proctoring_engine


@exam_bp.route("/analyze-frame", methods=["POST"])
@student_login_required
def analyze_frame():
    """Analyze a webcam frame for proctoring violations."""
    data = request.get_json()
    if not data or "frame" not in data:
        return jsonify({"success": False, "error": "No frame data"}), 400

    student = Student.query.get(session["student_id"])
    exam_id = data.get("exam_id") or session.get("current_exam_id")

    if not student or not exam_id:
        return jsonify({"success": False, "error": "Invalid session"}), 400

    # Load stored face encoding
    stored_encoding = None
    if student.face_encoding_path and os.path.exists(student.face_encoding_path):
        try:
            with open(student.face_encoding_path, "rb") as f:
                stored_encoding = pickle.load(f)
        except Exception:
            stored_encoding = None

    engine = _get_engine()
    analysis = engine.analyze_frame(data["frame"], stored_encoding)

    # Process violations
    violations_response = []
    if analysis.get("violations"):
        current_count = ViolationService.get_violation_count(student.id, exam_id)

        for v in analysis["violations"]:
            current_count += 1

            # Save screenshot
            screenshot_path = engine.save_screenshot(
                data["frame"],
                current_app.config["SCREENSHOTS_FOLDER"],
                student.student_id,
                v["type"],
            )

            # Record violation in DB
            ViolationService.record_violation(
                student_id=student.id,
                exam_id=exam_id,
                violation_type=v["type"],
                description=v["description"],
                confidence_score=v["confidence"],
                screenshot_path=screenshot_path,
                warning_number=current_count,
            )

            # Log activity
            ActivityService.log_activity(
                student.id, ActivityLog.VIOLATION,
                f"Violation: {v['label']}",
                extra_data={"type": v["type"], "confidence": v["confidence"]}
            )

            violations_response.append({
                "type": v["type"],
                "label": v["label"],
                "description": v["description"],
                "confidence": v["confidence"],
                "warning_number": current_count,
            })

    # Check if max warnings reached
    total_warnings = ViolationService.get_violation_count(student.id, exam_id)
    max_warnings = current_app.config.get("MAX_WARNINGS", 15)

    return jsonify({
        "success": True,
        "face_detected": analysis.get("face_detected", False),
        "face_count": analysis.get("face_count", 0),
        "violations": violations_response,
        "total_warnings": total_warnings,
        "max_warnings": max_warnings,
        "should_terminate": total_warnings >= max_warnings,
    })


@exam_bp.route("/browser-violation", methods=["POST"])
@student_login_required
def browser_violation():
    """Record a browser-based violation (tab switch, copy/paste, etc.)."""
    data = request.get_json()
    if not data or "type" not in data:
        return jsonify({"success": False, "error": "Missing violation type"}), 400

    student = Student.query.get(session["student_id"])
    exam_id = data.get("exam_id") or session.get("current_exam_id")

    if not student or not exam_id:
        return jsonify({"success": False, "error": "Invalid session"}), 400

    violation_type = data["type"]
    description = data.get("description", "")

    current_count = ViolationService.get_violation_count(student.id, exam_id) + 1

    # Save screenshot if provided
    screenshot_path = None
    if data.get("screenshot"):
        engine = _get_engine()
        screenshot_path = engine.save_screenshot(
            data["screenshot"],
            current_app.config["SCREENSHOTS_FOLDER"],
            student.student_id,
            violation_type,
        )

    ViolationService.record_violation(
        student_id=student.id,
        exam_id=exam_id,
        violation_type=violation_type,
        description=description,
        confidence_score=1.0,
        screenshot_path=screenshot_path,
        warning_number=current_count,
    )

    ActivityService.log_activity(
        student.id, ActivityLog.WARNING,
        f"Browser violation: {violation_type}",
    )

    total_warnings = ViolationService.get_violation_count(student.id, exam_id)
    max_warnings = current_app.config.get("MAX_WARNINGS", 15)

    return jsonify({
        "success": True,
        "warning_number": current_count,
        "total_warnings": total_warnings,
        "max_warnings": max_warnings,
        "should_terminate": total_warnings >= max_warnings,
    })


@exam_bp.route("/save-answer", methods=["POST"])
@student_login_required
def save_answer():
    """Save a student's answer to a question."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data"}), 400

    student_id = session["student_id"]
    exam_id = data.get("exam_id")
    question_id = data.get("question_id")
    selected_option = data.get("selected_option")

    if not all([exam_id, question_id, selected_option]):
        return jsonify({"success": False, "error": "Missing required fields"}), 400

    success, message = ExamService.save_answer(student_id, exam_id, question_id, selected_option)
    return jsonify({"success": success, "message": message})


@exam_bp.route("/submit", methods=["POST"])
@student_login_required
def submit_exam():
    """Submit the exam and generate report."""
    data = request.get_json()
    exam_id = data.get("exam_id") or session.get("current_exam_id")
    student_id = session["student_id"]

    if not exam_id:
        return jsonify({"success": False, "error": "No exam ID"}), 400

    # Calculate results
    result = ExamService.submit_exam(student_id, exam_id)

    # Log exam submission
    ActivityService.log_activity(
        student_id, ActivityLog.EXAM_SUBMIT,
        f"Exam submitted. Score: {result.get('total_score')}/{result.get('total_marks')}",
        extra_data=result,
    )

    # Generate report
    report_path, report_success, report_message = ReportService.generate_report(
        student_id, exam_id, current_app.config["REPORTS_FOLDER"]
    )

    # Clear exam session
    session.pop("current_exam_id", None)
    session.pop("exam_start_time", None)

    return jsonify({
        "success": True,
        "result": result,
        "report_generated": report_success,
    })


@exam_bp.route("/terminate", methods=["POST"])
@student_login_required
def terminate_exam():
    """Terminate exam due to max violations."""
    data = request.get_json()
    exam_id = data.get("exam_id") or session.get("current_exam_id")
    student_id = session["student_id"]

    if not exam_id:
        return jsonify({"success": False, "error": "No exam ID"}), 400

    # Record termination violation
    current_count = ViolationService.get_violation_count(student_id, exam_id) + 1
    ViolationService.record_violation(
        student_id=student_id,
        exam_id=exam_id,
        violation_type="exam_terminated",
        description="Exam auto-terminated due to exceeding maximum warnings.",
        confidence_score=1.0,
        warning_number=current_count,
    )

    # Log termination
    ActivityService.log_activity(
        student_id, ActivityLog.EXAM_TERMINATED,
        "Exam terminated due to excessive violations.",
    )

    # Calculate partial results
    result = ExamService.submit_exam(student_id, exam_id)

    # Generate report
    ReportService.generate_report(
        student_id, exam_id, current_app.config["REPORTS_FOLDER"]
    )

    # Clear exam session
    session.pop("current_exam_id", None)
    session.pop("exam_start_time", None)

    return jsonify({
        "success": True,
        "terminated": True,
        "result": result,
    })
