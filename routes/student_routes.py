"""
Student routes for dashboard, face capture, face verification, and exam pages.
"""

import os
import cv2
import numpy as np
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app

from utils.decorators import student_login_required, face_registered_required
from services.activity_service import ActivityService
from services.exam_service import ExamService
from services.violation_service import ViolationService
from models.student import Student
from models.activity_log import ActivityLog
from models.exam import Exam
from database.db import db
from utils.helpers import save_base64_image, generate_unique_filename
from vision.face_recognizer import FaceRecognizer

student_bp = Blueprint("student", __name__, url_prefix="/student")


@student_bp.route("/dashboard")
@student_login_required
def dashboard():
    """Student dashboard page."""
    student = Student.query.get(session["student_id"])
    exams = ExamService.get_active_exams()
    activities = ActivityService.get_student_activities(student.id, limit=10)
    violations_count = ViolationService.get_violation_count(student.id, exam_id=None)

    return render_template(
        "student/dashboard.html",
        student=student,
        exams=exams,
        activities=activities,
        violations_count=violations_count,
    )


@student_bp.route("/face-capture", methods=["GET", "POST"])
@student_login_required
def face_capture():
    """Face image capture and encoding page."""
    student = Student.query.get(session["student_id"])
    return render_template("student/face_capture.html", student=student)


@student_bp.route("/face-capture/save", methods=["POST"])
@student_login_required
def save_face():
    """Save captured face image and generate encoding."""
    student = Student.query.get(session["student_id"])
    data = request.get_json()

    if not data or "image" not in data:
        return {"success": False, "message": "No image data received."}, 400

    image_base64 = data["image"]

    # Save face image
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{student.student_id}_face.jpg"
    image_path = os.path.join(upload_dir, filename)

    if not save_base64_image(image_base64, image_path):
        return {"success": False, "message": "Failed to save image."}, 500

    # Generate face encoding
    recognizer = FaceRecognizer(tolerance=current_app.config.get("FACE_RECOGNITION_TOLERANCE", 0.5))
    encoding, success, message = recognizer.generate_encoding_from_file(image_path)

    if not success:
        os.remove(image_path)
        return {"success": False, "message": message}, 400

    # Save encoding
    encoding_dir = current_app.config["ENCODINGS_FOLDER"]
    os.makedirs(encoding_dir, exist_ok=True)
    encoding_path = os.path.join(encoding_dir, f"{student.student_id}_encoding.pkl")

    if not recognizer.save_encoding(encoding, encoding_path):
        return {"success": False, "message": "Failed to save face encoding."}, 500

    # Update student record
    student.face_image_path = image_path
    student.face_encoding_path = encoding_path
    student.is_face_registered = True
    db.session.commit()

    session["is_face_registered"] = True

    ActivityService.log_activity(
        student.id, ActivityLog.FACE_CAPTURE,
        "Face image captured and encoding generated."
    )

    return {"success": True, "message": "Face registered successfully!"}


@student_bp.route("/face-verify/<int:exam_id>")
@student_login_required
@face_registered_required
def face_verify(exam_id):
    """Face verification page before starting exam."""
    student = Student.query.get(session["student_id"])
    exam = ExamService.get_exam_by_id(exam_id)
    if not exam:
        flash("Exam not found.", "danger")
        return redirect(url_for("student.dashboard"))

    return render_template("student/face_verify.html", student=student, exam=exam)


@student_bp.route("/face-verify/check", methods=["POST"])
@student_login_required
def verify_face_check():
    """Verify face against stored encoding via AJAX."""
    student = Student.query.get(session["student_id"])
    data = request.get_json()

    if not data or "image" not in data:
        return {"success": False, "message": "No image data received."}, 400

    if not student.face_encoding_path or not os.path.exists(student.face_encoding_path):
        return {"success": False, "message": "Face encoding not found. Please register your face first."}, 400

    # Decode base64 image
    import base64
    image_base64 = data["image"]
    if "," in image_base64:
        image_base64 = image_base64.split(",")[1]
    img_bytes = base64.b64decode(image_base64)
    np_arr = np.frombuffer(img_bytes, dtype=np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if frame is None:
        return {"success": False, "message": "Failed to process image."}, 400

    recognizer = FaceRecognizer(tolerance=current_app.config.get("FACE_RECOGNITION_TOLERANCE", 0.5))
    stored_encoding = recognizer.load_encoding(student.face_encoding_path)

    if stored_encoding is None:
        return {"success": False, "message": "Failed to load face encoding."}, 500

    is_match, confidence, message = recognizer.verify_face(frame, stored_encoding)

    ActivityService.log_activity(
        student.id, ActivityLog.FACE_VERIFY,
        f"Face verification: {'Success' if is_match else 'Failed'} (confidence: {confidence:.2f})"
    )

    return {
        "success": is_match,
        "confidence": round(confidence, 2),
        "message": message,
    }


@student_bp.route("/exam/<int:exam_id>")
@student_login_required
@face_registered_required
def exam_page(exam_id):
    """Exam page with questions and proctoring."""
    student = Student.query.get(session["student_id"])
    exam = ExamService.get_exam_by_id(exam_id)
    if not exam:
        flash("Exam not found.", "danger")
        return redirect(url_for("student.dashboard"))

    questions = ExamService.get_exam_questions(exam_id)

    # Log exam start
    ActivityService.log_activity(
        student.id, ActivityLog.EXAM_START,
        f"Started exam: {exam.title}",
        extra_data={"exam_id": exam_id}
    )

    # Store exam info in session
    session["current_exam_id"] = exam_id
    session["exam_start_time"] = __import__("datetime").datetime.utcnow().isoformat()

    max_warnings = current_app.config.get("MAX_WARNINGS", 15)

    return render_template(
        "student/exam.html",
        student=student,
        exam=exam,
        questions=questions,
        max_warnings=max_warnings,
    )
