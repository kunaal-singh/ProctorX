
# 🛡️ ProctorX – Intelligent Online Examination Proctoring System

ProctorX is an AI-powered online examination proctoring system that authenticates students using facial recognition and continuously monitors examination sessions through real-time computer vision. The system detects suspicious activities such as unknown faces, multiple faces, face absence, head pose deviation, eye gaze abnormalities, phone usage, and browser violations while automatically capturing evidence, logging violations, and generating detailed PDF reports for administrators.

---

## 🚀 Features

### Student Module
- Student Registration & Login
- Face Image Capture & Encoding Generation
- Face Verification before Exam
- MCQ-based Exam with Timer
- Live Webcam Proctoring

### Exam Monitoring (Real-time AI)
- **Face Detection** — Haar Cascade + MediaPipe
- **Face Recognition** — dlib-based identity verification
- **Unknown Face Detection** — flags unregistered faces
- **Multiple Face Detection** — detects extra persons
- **Face Missing Detection** — alerts when face is absent
- **Face Blur Detection** — Laplacian variance analysis
- **Head Pose Estimation** — solvePnP-based yaw/pitch tracking
- **Eye Gaze Detection** — MediaPipe iris landmark tracking
- **Phone Detection** — YOLOv3-tiny or heuristic fallback
- **Tab Switch Detection** — Page Visibility API
- **Fullscreen Enforcement** — detects exit from fullscreen
- **Copy/Paste Prevention** — blocks clipboard events
- **Right-Click Disable** — blocks context menu
- **Keyboard Shortcut Blocking** — blocks Ctrl+C/V/U, F12, etc.

### Violation System
- Warning popup on each violation
- Screenshot capture & storage
- Violation database logging with timestamp & confidence
- Warning counter with progress bar
- Auto-termination after configurable max warnings

### Admin Module
- Admin Dashboard with Statistics
- Student Management (view, search, delete)
- Violation Log with Filtering
- Activity Logs
- Report Generation & Download
- Analytics Charts (Chart.js)

### PDF Report Generation (ReportLab)
- Student Details with Photograph
- Exam Information & Timing
- Score & Result
- Violation Log Table
- Pie & Bar Charts
- Violation Screenshots
- Integrity Summary

---

## 📁 Project Structure

```
ProctorX/
├── app.py                  # Flask application entry point
├── config.py               # Configuration & settings
├── requirements.txt        # Python dependencies
├── README.md
├── database/
│   ├── __init__.py
│   └── db.py               # SQLAlchemy initialization & seeding
├── models/
│   ├── student.py           # Student model
│   ├── admin.py             # Admin model
│   ├── exam.py              # Exam, Question, Answer models
│   ├── violation.py         # Violation model
│   ├── activity_log.py      # Activity log model
│   └── report.py            # Report model
├── routes/
│   ├── auth_routes.py       # Login, registration, logout
│   ├── student_routes.py    # Student dashboard, face capture, exam
│   ├── exam_routes.py       # Exam API (frame analysis, answers, submit)
│   └── admin_routes.py      # Admin dashboard, student mgmt, reports
├── services/
│   ├── auth_service.py      # Authentication logic
│   ├── exam_service.py      # Exam logic
│   ├── violation_service.py # Violation management
│   ├── activity_service.py  # Activity logging
│   └── report_service.py    # PDF report generation
├── vision/
│   ├── face_detector.py     # Haar + MediaPipe face detection
│   ├── face_recognizer.py   # dlib face recognition
│   ├── head_pose.py         # Head pose estimation
│   ├── eye_gaze.py          # Eye gaze & blink detection
│   ├── blur_detector.py     # Laplacian blur detection
│   ├── phone_detector.py    # YOLO phone detection
│   └── proctoring_engine.py # Central proctoring orchestrator
├── templates/               # Jinja2 HTML templates
├── static/
│   ├── css/style.css        # Dark theme with glassmorphism
│   └── js/
│       ├── main.js          # Shared utilities
│       ├── face_capture.js  # Face registration
│       ├── proctoring.js    # Exam proctoring engine
│       └── admin.js         # Admin charts
├── uploads/                 # Student face images
├── encodings/               # Face encoding files
├── screenshots/             # Violation screenshots
├── reports/                 # Generated PDF reports
├── logs/                    # Application logs
├── utils/
│   ├── decorators.py        # Auth decorators
│   └── helpers.py           # Utility functions
└── tests/                   # Test suite
```

---

## ⚙️ Installation

### Prerequisites
- Python 3.12+
- pip
- CMake (required for dlib)
- Visual Studio Build Tools (Windows) or build-essential (Linux)

### Steps

1. **Clone & Enter Directory**
   ```bash
   cd ProctorX
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate    # Linux/Mac
   venv\Scripts\activate       # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application**
   ```bash
   python app.py
   ```

5. **Access the App**
   - Student Portal: `http://localhost:5000/student/login`
   - Admin Panel: `http://localhost:5000/admin/login`

### Default Admin Credentials
- **Username:** admin
- **Password:** admin123

---

## 📷 YOLO Phone Detection (Optional)

For YOLOv3-tiny phone detection, download these files to the `vision/` directory:

1. **yolov3-tiny.cfg** — [GitHub darknet](https://github.com/pjreddie/darknet/blob/master/cfg/yolov3-tiny.cfg)
2. **yolov3-tiny.weights** — [pjreddie.com](https://pjreddie.com/media/files/yolov3-tiny.weights)
3. **coco.names** — [GitHub darknet](https://github.com/pjreddie/darknet/blob/master/data/coco.names)

If these files are not present, the system uses a heuristic-based fallback detector.

---

## 🛠️ Configuration

Edit `config.py` to customize:

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_WARNINGS` | 15 | Warnings before auto-termination |
| `FACE_RECOGNITION_TOLERANCE` | 0.5 | Face match distance threshold |
| `HEAD_POSE_YAW_THRESHOLD` | 30° | Max head yaw angle |
| `HEAD_POSE_PITCH_THRESHOLD` | 25° | Max head pitch angle |
| `EYE_GAZE_THRESHOLD` | 0.25 | Gaze deviation threshold |
| `BLUR_THRESHOLD` | 80.0 | Laplacian variance threshold |

---

## 🧪 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, Flask, SQLAlchemy, SQLite |
| Frontend | HTML5, CSS3, Bootstrap 5, JavaScript, AJAX |
| Computer Vision | OpenCV, face_recognition, dlib, MediaPipe |
| Reports | ReportLab |
| Charts | Chart.js |
| Auth | Flask Sessions, Werkzeug Password Hashing |

---

## 📄 License

This project is for educational and demonstration purposes.

---

## 👨‍💻 Author

**Kunal Singh**

**ProctorX – Intelligent Online Examination Proctoring System**

Built using:

- Python
- Flask
- OpenCV
- face_recognition
- MediaPipe
- SQLite
- HTML5
- CSS3
- JavaScript
- Bootstrap
- ReportLab



