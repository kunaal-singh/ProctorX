"""
Report generation service using ReportLab.
Produces professional PDF proctoring reports with charts, screenshots, and summaries.
"""

import os
import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor, black, white, grey
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, PageBreak, HRFlowable,
)
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart

from database.db import db
from models.student import Student
from models.exam import Exam, ExamAnswer
from models.violation import Violation
from models.activity_log import ActivityLog
from models.report import Report
from services.violation_service import ViolationService
from services.activity_service import ActivityService
from services.exam_service import ExamService
from utils.helpers import format_datetime, format_duration


# Color palette
PRIMARY = HexColor("#6C5CE7")
SECONDARY = HexColor("#00B894")
DANGER = HexColor("#D63031")
WARNING_COLOR = HexColor("#FDCB6E")
INFO = HexColor("#0984E3")
DARK = HexColor("#2D3436")
LIGHT_BG = HexColor("#F8F9FA")
BORDER_COLOR = HexColor("#DEE2E6")


class ReportService:
    """Service for generating professional PDF proctoring reports."""

    @staticmethod
    def generate_report(student_id, exam_id, reports_folder):
        """Generate a complete proctoring report as PDF.

        Args:
            student_id: Student database ID.
            exam_id: Exam database ID.
            reports_folder: Folder to save the report.

        Returns:
            Tuple of (report_path, success, message).
        """
        student = Student.query.get(student_id)
        exam = Exam.query.get(exam_id)

        if not student or not exam:
            return None, False, "Student or Exam not found."

        # Gather data
        violations = ViolationService.get_student_violations(student_id, exam_id)
        exam_times = ActivityService.get_student_exam_times(student_id)
        exam_result = ExamService.submit_exam(student_id, exam_id)
        answers = ExamService.get_student_answers(student_id, exam_id)

        # Build filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{student.student_id}_{exam_id}_{timestamp}.pdf"
        os.makedirs(reports_folder, exist_ok=True)
        filepath = os.path.join(reports_folder, filename)

        # Generate PDF
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=40,
            bottomMargin=40,
        )

        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Title"],
            fontSize=22,
            textColor=PRIMARY,
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        )
        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=DARK,
            spaceBefore=16,
            spaceAfter=8,
            fontName="Helvetica-Bold",
        )
        normal_style = ParagraphStyle(
            "CustomNormal",
            parent=styles["Normal"],
            fontSize=10,
            textColor=DARK,
            spaceAfter=4,
        )
        small_style = ParagraphStyle(
            "CustomSmall",
            parent=styles["Normal"],
            fontSize=8,
            textColor=grey,
        )

        elements = []

        # ── Title Section ──
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("🛡️ AI-Based Examination Proctoring Report", title_style))
        elements.append(Spacer(1, 4))
        elements.append(HRFlowable(width="100%", thickness=2, color=PRIMARY))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(
            f"Generated on: {datetime.now().strftime('%d %B %Y, %I:%M %p')}",
            ParagraphStyle("center_small", parent=small_style, alignment=TA_CENTER)
        ))
        elements.append(Spacer(1, 16))

        # ── Student Details ──
        elements.append(Paragraph("📋 Student Information", heading_style))
        student_data = [
            ["Field", "Details"],
            ["Student ID", student.student_id],
            ["Full Name", student.full_name],
            ["Email", student.email],
            ["Department", student.department or "N/A"],
            ["Semester", student.semester or "N/A"],
            ["Phone", student.phone or "N/A"],
            ["Face Registered", "Yes" if student.is_face_registered else "No"],
        ]
        student_table = Table(student_data, colWidths=[150, 350])
        student_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BACKGROUND", (0, 1), (0, -1), LIGHT_BG),
            ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ]))
        elements.append(student_table)
        elements.append(Spacer(1, 12))

        # ── Student Photograph ──
        if student.face_image_path and os.path.exists(student.face_image_path):
            elements.append(Paragraph("📸 Student Photograph", heading_style))
            try:
                img = RLImage(student.face_image_path, width=1.5*inch, height=1.5*inch)
                img.hAlign = "LEFT"
                elements.append(img)
            except Exception:
                elements.append(Paragraph("(Photograph could not be loaded)", normal_style))
            elements.append(Spacer(1, 12))

        # ── Exam Information ──
        elements.append(Paragraph("📝 Exam Information", heading_style))
        exam_data = [
            ["Field", "Details"],
            ["Exam Title", exam.title],
            ["Duration", f"{exam.duration_minutes} minutes"],
            ["Total Marks", str(exam.total_marks)],
            ["Passing Marks", str(exam.passing_marks)],
        ]
        exam_table = Table(exam_data, colWidths=[150, 350])
        exam_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), INFO),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BACKGROUND", (0, 1), (0, -1), LIGHT_BG),
            ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ]))
        elements.append(exam_table)
        elements.append(Spacer(1, 12))

        # ── Session Timing ──
        elements.append(Paragraph("⏱️ Session Timing", heading_style))
        timing_data = [
            ["Event", "Timestamp"],
            ["Login Time", format_datetime(exam_times.get("login_time"))],
            ["Exam Start", format_datetime(exam_times.get("exam_start_time"))],
            ["Exam End", format_datetime(exam_times.get("exam_end_time"))],
            ["Logout Time", format_datetime(exam_times.get("logout_time"))],
            ["Duration", format_duration(
                exam_times.get("exam_start_time"), exam_times.get("exam_end_time")
            )],
        ]
        timing_table = Table(timing_data, colWidths=[150, 350])
        timing_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), SECONDARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BACKGROUND", (0, 1), (0, -1), LIGHT_BG),
            ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ]))
        elements.append(timing_table)
        elements.append(Spacer(1, 12))

        # ── Exam Result ──
        elements.append(Paragraph("🏆 Exam Result", heading_style))
        result_color = SECONDARY if exam_result.get("is_passed") else DANGER
        result_text = "PASSED ✅" if exam_result.get("is_passed") else "FAILED ❌"
        result_data = [
            ["Metric", "Value"],
            ["Score", f"{exam_result.get('total_score', 0)} / {exam_result.get('total_marks', 0)}"],
            ["Percentage", f"{exam_result.get('percentage', 0)}%"],
            ["Questions Answered", f"{exam_result.get('answered_count', 0)} / {exam_result.get('total_questions', 0)}"],
            ["Correct Answers", str(exam_result.get("correct_count", 0))],
            ["Result", result_text],
            ["Total Violations", str(len(violations))],
        ]
        result_table = Table(result_data, colWidths=[150, 350])
        result_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), result_color),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BACKGROUND", (0, 1), (0, -1), LIGHT_BG),
            ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ]))
        elements.append(result_table)
        elements.append(Spacer(1, 16))

        # ── Violation Summary Chart ──
        if violations:
            elements.append(PageBreak())
            elements.append(Paragraph("📊 Violation Analysis", heading_style))

            # Count violations by type
            v_counts = {}
            for v in violations:
                v_counts[v.violation_type] = v_counts.get(v.violation_type, 0) + 1

            # Pie Chart
            drawing = Drawing(400, 200)
            pie = Pie()
            pie.x = 100
            pie.y = 10
            pie.width = 150
            pie.height = 150
            pie.data = list(v_counts.values())
            pie.labels = [f"{k} ({v})" for k, v in v_counts.items()]

            chart_colors = [
                HexColor("#6C5CE7"), HexColor("#00B894"), HexColor("#D63031"),
                HexColor("#FDCB6E"), HexColor("#0984E3"), HexColor("#E17055"),
                HexColor("#00CEC9"), HexColor("#FD79A8"),
            ]
            for i in range(len(pie.data)):
                pie.slices[i].fillColor = chart_colors[i % len(chart_colors)]
                pie.slices[i].strokeColor = white
                pie.slices[i].strokeWidth = 1

            drawing.add(pie)
            elements.append(drawing)
            elements.append(Spacer(1, 16))

            # Bar Chart
            if len(v_counts) > 1:
                bar_drawing = Drawing(500, 200)
                bc = VerticalBarChart()
                bc.x = 60
                bc.y = 30
                bc.width = 380
                bc.height = 140
                bc.data = [list(v_counts.values())]
                bc.categoryAxis.categoryNames = list(v_counts.keys())
                bc.categoryAxis.labels.angle = 30
                bc.categoryAxis.labels.fontSize = 7
                bc.valueAxis.valueMin = 0
                bc.valueAxis.valueMax = max(v_counts.values()) + 2
                bc.bars[0].fillColor = PRIMARY
                bar_drawing.add(bc)
                elements.append(bar_drawing)
                elements.append(Spacer(1, 16))

            # ── Violations Detail Table ──
            elements.append(Paragraph("🚨 Violations Log", heading_style))
            v_header = ["#", "Type", "Description", "Confidence", "Severity", "Timestamp"]
            v_rows = [v_header]
            for idx, v in enumerate(violations, 1):
                v_rows.append([
                    str(idx),
                    v.violation_type,
                    (v.description or "")[:40],
                    f"{v.confidence_score:.0%}" if v.confidence_score else "N/A",
                    v.severity,
                    v.timestamp.strftime("%H:%M:%S") if v.timestamp else "N/A",
                ])

            v_table = Table(v_rows, colWidths=[30, 90, 150, 65, 60, 70])
            v_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), DANGER),
                ("TEXTCOLOR", (0, 0), (-1, 0), white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, LIGHT_BG]),
            ]))
            elements.append(v_table)
            elements.append(Spacer(1, 16))

            # ── Violation Screenshots ──
            screenshot_violations = [v for v in violations if v.screenshot_path and os.path.exists(v.screenshot_path)]
            if screenshot_violations:
                elements.append(PageBreak())
                elements.append(Paragraph("📷 Violation Screenshots", heading_style))
                for v in screenshot_violations[:10]:  # Limit to 10 screenshots
                    elements.append(Paragraph(
                        f"<b>{v.violation_type}</b> — {v.timestamp.strftime('%H:%M:%S') if v.timestamp else 'N/A'}",
                        normal_style
                    ))
                    try:
                        img = RLImage(v.screenshot_path, width=4*inch, height=3*inch)
                        img.hAlign = "LEFT"
                        elements.append(img)
                    except Exception:
                        elements.append(Paragraph("(Screenshot could not be loaded)", small_style))
                    elements.append(Spacer(1, 10))

        # ── Summary ──
        elements.append(Spacer(1, 20))
        elements.append(HRFlowable(width="100%", thickness=1, color=BORDER_COLOR))
        elements.append(Spacer(1, 10))

        integrity_status = "CLEAN" if len(violations) == 0 else (
            "FLAGGED" if len(violations) < 5 else "SUSPICIOUS"
        )
        integrity_color = SECONDARY if integrity_status == "CLEAN" else (
            WARNING_COLOR if integrity_status == "FLAGGED" else DANGER
        )

        summary_style = ParagraphStyle(
            "Summary",
            parent=styles["Normal"],
            fontSize=12,
            textColor=DARK,
            alignment=TA_CENTER,
            spaceAfter=8,
        )
        elements.append(Paragraph(f"<b>Exam Integrity Status: {integrity_status}</b>", summary_style))
        elements.append(Paragraph(
            f"Total Violations: {len(violations)} | "
            f"Score: {exam_result.get('total_score', 0)}/{exam_result.get('total_marks', 0)} | "
            f"Result: {result_text}",
            summary_style
        ))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(
            "This report was auto-generated by the AI-Based Online Examination Proctoring System.",
            ParagraphStyle("footer", parent=small_style, alignment=TA_CENTER)
        ))

        # Build PDF
        doc.build(elements)

        # Save report record in DB
        try:
            report = Report(
                student_id=student_id,
                exam_id=exam_id,
                report_path=filepath,
                total_violations=len(violations),
                total_warnings=len(violations),
                exam_score=exam_result.get("total_score", 0),
                total_marks=exam_result.get("total_marks", 0),
                exam_status="completed",
                is_passed=exam_result.get("is_passed", False),
                exam_start_time=exam_times.get("exam_start_time"),
                exam_end_time=exam_times.get("exam_end_time"),
            )
            db.session.add(report)
            db.session.commit()
        except Exception:
            db.session.rollback()

        return filepath, True, "Report generated successfully."

    @staticmethod
    def get_student_reports(student_id):
        """Get all reports for a student.

        Args:
            student_id: Student database ID.

        Returns:
            List of Report objects.
        """
        return Report.query.filter_by(student_id=student_id).order_by(
            Report.generated_at.desc()
        ).all()

    @staticmethod
    def get_all_reports(limit=100):
        """Get all reports.

        Args:
            limit: Maximum results.

        Returns:
            List of Report objects.
        """
        return Report.query.order_by(Report.generated_at.desc()).limit(limit).all()

    @staticmethod
    def get_report_by_id(report_id):
        """Get a report by ID.

        Args:
            report_id: Report database ID.

        Returns:
            Report object or None.
        """
        return Report.query.get(report_id)
