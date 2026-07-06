"""
Database initialization and session management.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    """Initialize the database with the Flask application."""
    db.init_app(app)
    with app.app_context():
        from models.student import Student
        from models.admin import Admin
        from models.exam import Exam, ExamQuestion, ExamAnswer
        from models.violation import Violation
        from models.activity_log import ActivityLog
        from models.report import Report
        db.create_all()
        _seed_admin()
        _seed_exam_questions()


def _seed_admin():
    """Create default admin account if none exists."""
    from models.admin import Admin
    from werkzeug.security import generate_password_hash

    if Admin.query.count() == 0:
        admin = Admin(
            username="admin",
            password_hash=generate_password_hash("admin123"),
            full_name="System Administrator",
            email="admin@proctoring.local",
        )
        db.session.add(admin)
        db.session.commit()


def _seed_exam_questions():
    """Seed sample exam questions if none exist."""
    from models.exam import Exam, ExamQuestion

    if Exam.query.count() == 0:
        exam = Exam(
            title="General Knowledge Assessment",
            description="A comprehensive general knowledge test covering science, mathematics, and reasoning.",
            duration_minutes=30,
            total_marks=40,
            passing_marks=16,
            is_active=True,
        )
        db.session.add(exam)
        db.session.commit()

        questions = [
            {
                "question_text": "What is the chemical symbol for Gold?",
                "option_a": "Go",
                "option_b": "Au",
                "option_c": "Gd",
                "option_d": "Ag",
                "correct_option": "B",
                "marks": 2,
            },
            {
                "question_text": "Which planet is known as the Red Planet?",
                "option_a": "Venus",
                "option_b": "Jupiter",
                "option_c": "Mars",
                "option_d": "Saturn",
                "correct_option": "C",
                "marks": 2,
            },
            {
                "question_text": "What is the value of Pi (π) to two decimal places?",
                "option_a": "3.12",
                "option_b": "3.14",
                "option_c": "3.16",
                "option_d": "3.18",
                "correct_option": "B",
                "marks": 2,
            },
            {
                "question_text": "Who developed the Theory of Relativity?",
                "option_a": "Isaac Newton",
                "option_b": "Niels Bohr",
                "option_c": "Albert Einstein",
                "option_d": "Galileo Galilei",
                "correct_option": "C",
                "marks": 2,
            },
            {
                "question_text": "What is the largest organ in the human body?",
                "option_a": "Heart",
                "option_b": "Liver",
                "option_c": "Brain",
                "option_d": "Skin",
                "correct_option": "D",
                "marks": 2,
            },
            {
                "question_text": "What is the speed of light in vacuum (approx)?",
                "option_a": "3 × 10⁶ m/s",
                "option_b": "3 × 10⁸ m/s",
                "option_c": "3 × 10¹⁰ m/s",
                "option_d": "3 × 10⁴ m/s",
                "correct_option": "B",
                "marks": 2,
            },
            {
                "question_text": "Which data structure uses FIFO?",
                "option_a": "Stack",
                "option_b": "Queue",
                "option_c": "Tree",
                "option_d": "Graph",
                "correct_option": "B",
                "marks": 2,
            },
            {
                "question_text": "What is the powerhouse of the cell?",
                "option_a": "Nucleus",
                "option_b": "Ribosome",
                "option_c": "Mitochondria",
                "option_d": "Golgi Body",
                "correct_option": "C",
                "marks": 2,
            },
            {
                "question_text": "Which language is primarily used for AI/ML?",
                "option_a": "Java",
                "option_b": "Python",
                "option_c": "C++",
                "option_d": "Ruby",
                "correct_option": "B",
                "marks": 2,
            },
            {
                "question_text": "What does HTTP stand for?",
                "option_a": "HyperText Transfer Protocol",
                "option_b": "High Transfer Text Protocol",
                "option_c": "HyperText Transmission Process",
                "option_d": "High Text Transfer Protocol",
                "correct_option": "A",
                "marks": 2,
            },
            {
                "question_text": "What is the binary representation of the decimal number 10?",
                "option_a": "1010",
                "option_b": "1100",
                "option_c": "1001",
                "option_d": "1110",
                "correct_option": "A",
                "marks": 2,
            },
            {
                "question_text": "Which element has the atomic number 1?",
                "option_a": "Helium",
                "option_b": "Oxygen",
                "option_c": "Hydrogen",
                "option_d": "Carbon",
                "correct_option": "C",
                "marks": 2,
            },
            {
                "question_text": "What is the time complexity of binary search?",
                "option_a": "O(n)",
                "option_b": "O(n²)",
                "option_c": "O(log n)",
                "option_d": "O(1)",
                "correct_option": "C",
                "marks": 2,
            },
            {
                "question_text": "Which country is known as the Land of the Rising Sun?",
                "option_a": "China",
                "option_b": "South Korea",
                "option_c": "Japan",
                "option_d": "Thailand",
                "correct_option": "C",
                "marks": 2,
            },
            {
                "question_text": "What is the full form of SQL?",
                "option_a": "Structured Query Language",
                "option_b": "Simple Query Language",
                "option_c": "Sequential Query Logic",
                "option_d": "Standard Query Language",
                "correct_option": "A",
                "marks": 2,
            },
            {
                "question_text": "Which gas is most abundant in Earth's atmosphere?",
                "option_a": "Oxygen",
                "option_b": "Carbon Dioxide",
                "option_c": "Nitrogen",
                "option_d": "Argon",
                "correct_option": "C",
                "marks": 2,
            },
            {
                "question_text": "What is 2⁸?",
                "option_a": "128",
                "option_b": "256",
                "option_c": "512",
                "option_d": "64",
                "correct_option": "B",
                "marks": 2,
            },
            {
                "question_text": "Who is the father of Computer Science?",
                "option_a": "Charles Babbage",
                "option_b": "Alan Turing",
                "option_c": "John von Neumann",
                "option_d": "Dennis Ritchie",
                "correct_option": "B",
                "marks": 2,
            },
            {
                "question_text": "What does RAM stand for?",
                "option_a": "Read Access Memory",
                "option_b": "Random Access Memory",
                "option_c": "Rapid Access Module",
                "option_d": "Read And Modify",
                "correct_option": "B",
                "marks": 2,
            },
            {
                "question_text": "Which vitamin is produced when skin is exposed to sunlight?",
                "option_a": "Vitamin A",
                "option_b": "Vitamin B",
                "option_c": "Vitamin C",
                "option_d": "Vitamin D",
                "correct_option": "D",
                "marks": 2,
            },
        ]

        for idx, q_data in enumerate(questions, start=1):
            question = ExamQuestion(
                exam_id=exam.id,
                question_number=idx,
                question_text=q_data["question_text"],
                option_a=q_data["option_a"],
                option_b=q_data["option_b"],
                option_c=q_data["option_c"],
                option_d=q_data["option_d"],
                correct_option=q_data["correct_option"],
                marks=q_data["marks"],
            )
            db.session.add(question)

        db.session.commit()
