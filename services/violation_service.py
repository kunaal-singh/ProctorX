"""
Violation service for recording and managing exam violations.
"""

from datetime import datetime
from database.db import db
from models.violation import Violation


class ViolationService:
    """Service for violation management."""

    @staticmethod
    def record_violation(student_id, exam_id, violation_type, description="",
                         confidence_score=0.0, screenshot_path=None, warning_number=1):
        """Record a new violation.

        Args:
            student_id: Student database ID.
            exam_id: Exam database ID.
            violation_type: Type of violation.
            description: Description text.
            confidence_score: Detection confidence.
            screenshot_path: Path to violation screenshot.
            warning_number: Current warning count.

        Returns:
            Tuple of (violation, success, message).
        """
        try:
            severity = Violation.get_severity(violation_type)
            violation = Violation(
                student_id=student_id,
                exam_id=exam_id,
                violation_type=violation_type,
                description=description,
                confidence_score=confidence_score,
                screenshot_path=screenshot_path,
                warning_number=warning_number,
                severity=severity,
            )
            db.session.add(violation)
            db.session.commit()
            return violation, True, "Violation recorded."
        except Exception as e:
            db.session.rollback()
            import traceback
            with open("violation_error.log", "a") as f:
                f.write(f"ERROR: {str(e)}\n{traceback.format_exc()}\n")
            print(f"ERROR RECORDING VIOLATION: {str(e)}")
            return None, False, str(e)

    @staticmethod
    def get_student_violations(student_id, exam_id=None):
        """Get violations for a student.

        Args:
            student_id: Student database ID.
            exam_id: Optional exam ID to filter.

        Returns:
            List of Violation objects.
        """
        query = Violation.query.filter_by(student_id=student_id)
        if exam_id:
            query = query.filter_by(exam_id=exam_id)
        return query.order_by(Violation.timestamp.desc()).all()

    @staticmethod
    def get_violation_count(student_id, exam_id):
        """Get total violation count for a student in an exam.

        Args:
            student_id: Student database ID.
            exam_id: Exam database ID.

        Returns:
            Integer count.
        """
        return Violation.query.filter_by(
            student_id=student_id,
            exam_id=exam_id,
        ).count()

    @staticmethod
    def get_all_violations(limit=100, offset=0):
        """Get all violations with pagination.

        Args:
            limit: Maximum results.
            offset: Offset for pagination.

        Returns:
            List of Violation objects.
        """
        return Violation.query.order_by(
            Violation.timestamp.desc()
        ).offset(offset).limit(limit).all()

    @staticmethod
    def get_violation_statistics():
        """Get violation statistics.

        Returns:
            Dictionary with statistics.
        """
        total = Violation.query.count()
        by_type = db.session.query(
            Violation.violation_type,
            db.func.count(Violation.id)
        ).group_by(Violation.violation_type).all()

        by_severity = db.session.query(
            Violation.severity,
            db.func.count(Violation.id)
        ).group_by(Violation.severity).all()

        return {
            "total": total,
            "by_type": {vtype: count for vtype, count in by_type},
            "by_severity": {sev: count for sev, count in by_severity},
        }

    @staticmethod
    def delete_student_violations(student_id):
        """Delete all violations for a student.

        Args:
            student_id: Student database ID.

        Returns:
            Number of deleted violations.
        """
        count = Violation.query.filter_by(student_id=student_id).delete()
        db.session.commit()
        return count
