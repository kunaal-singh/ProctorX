"""
Helper utilities for the proctoring system.
"""

import os
import re
import uuid
import base64
import json
from datetime import datetime
from flask import request


def generate_student_id():
    """Generate a unique student ID."""
    return f"STU{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"


def allowed_file(filename, allowed_extensions=None):
    """Check if the file extension is allowed."""
    if allowed_extensions is None:
        allowed_extensions = {"png", "jpg", "jpeg"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def save_base64_image(base64_string, save_path):
    """Save a base64-encoded image to disk."""
    try:
        if "," in base64_string:
            base64_string = base64_string.split(",")[1]
        image_data = base64.b64decode(base64_string)
        with open(save_path, "wb") as f:
            f.write(image_data)
        return True
    except Exception:
        return False


def base64_to_bytes(base64_string):
    """Convert base64 string to bytes."""
    if "," in base64_string:
        base64_string = base64_string.split(",")[1]
    return base64.b64decode(base64_string)


def image_to_base64(image_path):
    """Convert an image file to base64 string."""
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return None


def get_client_ip():
    """Get client IP address from request."""
    if request.environ.get("HTTP_X_FORWARDED_FOR"):
        return request.environ["HTTP_X_FORWARDED_FOR"].split(",")[0].strip()
    return request.environ.get("REMOTE_ADDR", "unknown")


def get_user_agent():
    """Get user agent string from request."""
    return request.headers.get("User-Agent", "unknown")[:256]


def sanitize_filename(filename):
    """Sanitize a filename to prevent path traversal attacks."""
    filename = re.sub(r'[^\w\s\-.]', '', filename)
    filename = filename.strip()
    return filename if filename else "unnamed"


def format_datetime(dt):
    """Format datetime object to readable string."""
    if dt is None:
        return "N/A"
    return dt.strftime("%d %b %Y, %I:%M %p")


def format_duration(start, end):
    """Format duration between two datetime objects."""
    if not start or not end:
        return "N/A"
    delta = end - start
    total_seconds = int(delta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    if minutes > 0:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


def generate_unique_filename(extension="png"):
    """Generate a unique filename with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    return f"{timestamp}_{unique_id}.{extension}"


def parse_json_safe(json_string, default=None):
    """Safely parse a JSON string."""
    if default is None:
        default = {}
    try:
        return json.loads(json_string) if json_string else default
    except (json.JSONDecodeError, TypeError):
        return default
