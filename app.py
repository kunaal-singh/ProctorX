"""
AI-Based Online Examination Proctoring System
Main application entry point.
"""

import os
import sys

# Ensure project root is in Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from flask import Flask, render_template
from config import Config, config_by_name
from database.db import init_db


def create_app(config_name="development"):
    """Application factory.

    Args:
        config_name: Configuration name ('development', 'production', 'testing').

    Returns:
        Configured Flask application.
    """
    app = Flask(__name__)

    # Load configuration
    app_config = config_by_name.get(config_name, Config)
    app.config.from_object(app_config)

    # Initialize directories
    Config.init_app(app)

    # Initialize database
    init_db(app)

    # Register blueprints
    from routes.auth_routes import auth_bp
    from routes.student_routes import student_bp
    from routes.exam_routes import exam_bp
    from routes.admin_routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(exam_bp)
    app.register_blueprint(admin_bp)

    # Index route
    @app.route("/")
    def index():
        return render_template("index.html")

    # Register error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template("base.html", error_code=404, error_message="Page Not Found"), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template("base.html", error_code=500, error_message="Internal Server Error"), 500

    return app


if __name__ == "__main__":
    app = create_app("development")
    app.run(host="0.0.0.0", port=8080, debug=True)