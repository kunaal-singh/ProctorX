"""
Activity logging service for tracking all user activities.
"""

import json
from datetime import datetime
from database.db import db
from models.activity_log import ActivityLog
from utils.helpers import get_client_ip, get_user_agent


class ActivityService:
    """Service for activity logging."""

    @staticmethod
    def log_activity(student_id, activity_type, description="", extra_data=None):
        """Log a student activity.

        Args:
            student_id: Student database ID (can be None for system events).
            activity_type: Type of activity (use ActivityLog constants).
            description: Human-readable description.
            extra_data: Optional dictionary of additional data.

        Returns:
            ActivityLog object.
        """
        try:
            log = ActivityLog(
                student_id=student_id,
                activity_type=activity_type,
                description=description,
                ip_address=get_client_ip(),
                user_agent=get_user_agent(),
                extra_data=json.dumps(extra_data) if extra_data else None,
            )
            db.session.add(log)
            db.session.commit()
            return log
        except Exception:
            db.session.rollback()
            return None

    @staticmethod
    def get_student_activities(student_id, limit=50):
        """Get activity logs for a student.

        Args:
            student_id: Student database ID.
            limit: Maximum results.

        Returns:
            List of ActivityLog objects.
        """
        return ActivityLog.query.filter_by(
            student_id=student_id
        ).order_by(ActivityLog.timestamp.desc()).limit(limit).all()

    @staticmethod
    def get_all_activities(limit=100, offset=0, activity_type=None):
        """Get all activity logs.

        Args:
            limit: Maximum results.
            offset: Offset for pagination.
            activity_type: Optional filter by activity type.

        Returns:
            List of ActivityLog objects.
        """
        query = ActivityLog.query
        if activity_type:
            query = query.filter_by(activity_type=activity_type)
        return query.order_by(ActivityLog.timestamp.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def get_student_exam_times(student_id, exam_id=None):
        """Get exam start and end times for a student.

        Args:
            student_id: Student database ID.
            exam_id: Optional exam ID.

        Returns:
            Dictionary with start and end times.
        """
        start_log = ActivityLog.query.filter_by(
            student_id=student_id,
            activity_type=ActivityLog.EXAM_START,
        ).order_by(ActivityLog.timestamp.desc()).first()

        end_log = ActivityLog.query.filter(
            ActivityLog.student_id == student_id,
            ActivityLog.activity_type.in_([
                ActivityLog.EXAM_END,
                ActivityLog.EXAM_SUBMIT,
                ActivityLog.EXAM_TERMINATED,
            ]),
        ).order_by(ActivityLog.timestamp.desc()).first()

        login_log = ActivityLog.query.filter_by(
            student_id=student_id,
            activity_type=ActivityLog.LOGIN,
        ).order_by(ActivityLog.timestamp.desc()).first()

        logout_log = ActivityLog.query.filter_by(
            student_id=student_id,
            activity_type=ActivityLog.LOGOUT,
        ).order_by(ActivityLog.timestamp.desc()).first()

        return {
            "login_time": login_log.timestamp if login_log else None,
            "logout_time": logout_log.timestamp if logout_log else None,
            "exam_start_time": start_log.timestamp if start_log else None,
            "exam_end_time": end_log.timestamp if end_log else None,
        }

    @staticmethod
    def get_activity_count():
        """Get total activity count.

        Returns:
            Integer count.
        """
        return ActivityLog.query.count()

    @staticmethod
    def get_recent_activities(limit=20):
        """Get most recent activities.

        Args:
            limit: Maximum results.

        Returns:
            List of ActivityLog objects.
        """
        return ActivityLog.query.order_by(
            ActivityLog.timestamp.desc()
        ).limit(limit).all()
