/**
 * Proctoring Engine JavaScript
 * Handles all exam-time proctoring: camera analysis, browser monitoring,
 * question navigation, timer, answer saving, and exam submission.
 */

// ── State ──
let proctoringStream = null;
let currentQuestion = 1;
let totalQuestions = 0;
let examId = 0;
let maxWarnings = 15;
let warningCount = 0;
let examDuration = 0;
let timerInterval = null;
let analysisInterval = null;
let timeRemaining = 0;
let answeredQuestions = new Set();
let isExamActive = true;

// ── Initialize ──
document.addEventListener('DOMContentLoaded', () => {
    examId = parseInt(document.getElementById('examId').value);
    maxWarnings = parseInt(document.getElementById('maxWarnings').value);
    examDuration = parseInt(document.getElementById('examDuration').value);
    totalQuestions = parseInt(document.getElementById('totalQuestions').value);
    timeRemaining = examDuration * 60;

    // Start camera
    startProctoringCamera();

    // Start timer
    startTimer();

    // Setup browser monitoring
    setupBrowserMonitoring();

    // Request fullscreen
    requestFullscreen();
});

// ── Camera ──
function startProctoringCamera() {
    const video = document.getElementById('proctoringVideo');
    navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: 'user' }
    })
    .then(stream => {
        proctoringStream = stream;
        video.srcObject = stream;
        document.getElementById('cameraStatus').className = 'camera-status-dot bg-success';

        // Start analysis loop (every 5 seconds)
        analysisInterval = setInterval(analyzeFrame, 5000);
    })
    .catch(err => {
        document.getElementById('cameraStatus').className = 'camera-status-dot bg-danger';
        document.getElementById('faceStatusText').innerHTML =
            '<i class="bi bi-x-circle text-danger"></i> Camera Error';
        reportBrowserViolation('face_missing', 'Camera access denied or unavailable.');
    });
}

// ── Frame Analysis ──
function analyzeFrame() {
    if (!isExamActive || !proctoringStream) return;

    const video = document.getElementById('proctoringVideo');
    const canvas = document.getElementById('proctoringCanvas');
    const ctx = canvas.getContext('2d');

    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    ctx.drawImage(video, 0, 0);

    const frameData = canvas.toDataURL('image/jpeg', 0.7);

    fetch('/api/exam/analyze-frame', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            frame: frameData,
            exam_id: examId
        })
    })
    .then(res => res.json())
    .then(data => {
        if (!data.success) return;

        // Update face status
        updateFaceStatus(data.face_detected, data.face_count);

        // Process violations
        if (data.violations && data.violations.length > 0) {
            data.violations.forEach(v => {
                handleViolation(v);
            });
        }

        // Update warning count from server
        warningCount = data.total_warnings;
        updateWarningDisplay();

        // Check termination
        if (data.should_terminate) {
            terminateExam();
        }
    })
    .catch(err => {
        console.error('Frame analysis error:', err);
    });
}

function updateFaceStatus(detected, count) {
    const el = document.getElementById('faceStatusText');
    const statusFace = document.getElementById('statusFace');

    if (!detected || count === 0) {
        el.innerHTML = '<i class="bi bi-x-circle text-danger"></i> No Face Detected';
        statusFace.innerHTML = '<i class="bi bi-x-circle-fill text-danger"></i>';
    } else if (count > 1) {
        el.innerHTML = '<i class="bi bi-exclamation-circle text-warning"></i> Multiple Faces (' + count + ')';
        statusFace.innerHTML = '<i class="bi bi-exclamation-circle-fill text-warning"></i>';
    } else {
        el.innerHTML = '<i class="bi bi-check-circle text-success"></i> Face Detected';
        statusFace.innerHTML = '<i class="bi bi-check-circle-fill text-success"></i>';
    }
}

// ── Violation Handling ──
function handleViolation(violation) {
    warningCount = violation.warning_number || (warningCount + 1);
    updateWarningDisplay();
    showWarningPopup(violation.label || violation.type, violation.description || '');
}

function showWarningPopup(title, description) {
    document.getElementById('warningMessage').innerHTML =
        `<strong>${title}</strong><br><small class="text-muted">${description}</small>`;
    document.getElementById('modalWarningNum').textContent = warningCount;

    const pct = Math.min(100, (warningCount / maxWarnings) * 100);
    document.getElementById('modalProgress').style.width = pct + '%';

    const modalEl = document.getElementById('warningModal');
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();

    // Auto-close after 5 seconds
    setTimeout(() => {
        modal.hide();
    }, 5000);
}

function updateWarningDisplay() {
    document.getElementById('warningCount').textContent = warningCount;
    const pct = Math.min(100, Math.round((warningCount / maxWarnings) * 100));
    document.getElementById('warningPercent').textContent = pct;
    document.getElementById('warningProgress').style.width = pct + '%';

    // Change color based on severity
    const badge = document.getElementById('warningBadge');
    if (pct >= 80) {
        badge.className = 'badge bg-danger px-3 py-2 pulse-danger';
    } else if (pct >= 50) {
        badge.className = 'badge bg-warning text-dark px-3 py-2';
    }
}

// ── Browser Monitoring ──
function setupBrowserMonitoring() {
    // Tab switch / visibility change
    document.addEventListener('visibilitychange', () => {
        if (document.hidden && isExamActive) {
            reportBrowserViolation('tab_switch', 'Student switched to another tab or window.');
        }
    });

    // Window blur
    window.addEventListener('blur', () => {
        if (isExamActive) {
            updateStatusIndicator('statusBrowser', 'danger');
        }
    });
    window.addEventListener('focus', () => {
        updateStatusIndicator('statusBrowser', 'success');
    });

    // Fullscreen exit
    document.addEventListener('fullscreenchange', () => {
        if (!document.fullscreenElement && isExamActive) {
            reportBrowserViolation('fullscreen_exit', 'Student exited fullscreen mode.');
            // Re-request fullscreen
            setTimeout(requestFullscreen, 1000);
        }
    });

    // Copy/Paste prevention
    document.addEventListener('copy', (e) => {
        if (isExamActive) {
            e.preventDefault();
            reportBrowserViolation('copy_paste', 'Copy attempt blocked.');
        }
    });
    document.addEventListener('paste', (e) => {
        if (isExamActive) {
            e.preventDefault();
            reportBrowserViolation('copy_paste', 'Paste attempt blocked.');
        }
    });
    document.addEventListener('cut', (e) => {
        if (isExamActive) {
            e.preventDefault();
            reportBrowserViolation('copy_paste', 'Cut attempt blocked.');
        }
    });

    // Right-click disable
    document.addEventListener('contextmenu', (e) => {
        if (isExamActive) {
            e.preventDefault();
            reportBrowserViolation('right_click', 'Right-click attempt blocked.');
        }
    });

    // Keyboard shortcut blocking
    document.addEventListener('keydown', (e) => {
        if (!isExamActive) return;

        const blocked = [
            (e.ctrlKey && e.key === 'c'),
            (e.ctrlKey && e.key === 'v'),
            (e.ctrlKey && e.key === 'x'),
            (e.ctrlKey && e.key === 'a'),
            (e.ctrlKey && e.key === 'u'),
            (e.ctrlKey && e.key === 'p'),
            (e.ctrlKey && e.key === 's'),
            (e.ctrlKey && e.shiftKey && e.key === 'I'),
            (e.ctrlKey && e.shiftKey && e.key === 'J'),
            (e.ctrlKey && e.shiftKey && e.key === 'C'),
            (e.key === 'F12'),
            (e.key === 'PrintScreen'),
            (e.altKey && e.key === 'Tab'),
        ];

        if (blocked.some(b => b)) {
            e.preventDefault();
            e.stopPropagation();
            reportBrowserViolation('keyboard_shortcut',
                `Blocked keyboard shortcut: ${e.ctrlKey ? 'Ctrl+' : ''}${e.shiftKey ? 'Shift+' : ''}${e.altKey ? 'Alt+' : ''}${e.key}`);
        }
    });
}

function reportBrowserViolation(type, description) {
    if (!isExamActive) return;

    // Capture screenshot
    let screenshot = null;
    try {
        const video = document.getElementById('proctoringVideo');
        const canvas = document.getElementById('proctoringCanvas');
        const ctx = canvas.getContext('2d');
        canvas.width = video.videoWidth || 640;
        canvas.height = video.videoHeight || 480;
        ctx.drawImage(video, 0, 0);
        screenshot = canvas.toDataURL('image/jpeg', 0.7);
    } catch (e) {
        // Cannot capture screenshot
    }

    fetch('/api/exam/browser-violation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            type: type,
            description: description,
            exam_id: examId,
            screenshot: screenshot
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            warningCount = data.total_warnings;
            updateWarningDisplay();
            showWarningPopup(
                type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                description
            );

            if (data.should_terminate) {
                terminateExam();
            }
        }
    })
    .catch(err => console.error('Browser violation report error:', err));
}

function updateStatusIndicator(elementId, color) {
    const el = document.getElementById(elementId);
    if (el) {
        el.innerHTML = `<i class="bi bi-${color === 'success' ? 'check' : 'x'}-circle-fill text-${color}"></i>`;
    }
}

function requestFullscreen() {
    const el = document.documentElement;
    if (el.requestFullscreen) el.requestFullscreen().catch(() => {});
    else if (el.webkitRequestFullscreen) el.webkitRequestFullscreen();
    else if (el.msRequestFullscreen) el.msRequestFullscreen();
}

// ── Timer ──
function startTimer() {
    timerInterval = setInterval(() => {
        if (timeRemaining <= 0) {
            clearInterval(timerInterval);
            autoSubmitExam();
            return;
        }
        timeRemaining--;
        const minutes = Math.floor(timeRemaining / 60);
        const seconds = timeRemaining % 60;
        document.getElementById('timerDisplay').textContent =
            `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

        // Visual warnings when time is low
        const timerEl = document.getElementById('examTimer');
        if (timeRemaining <= 60) {
            timerEl.className = 'badge bg-danger px-3 py-2';
        } else if (timeRemaining <= 300) {
            timerEl.className = 'badge bg-warning text-dark px-3 py-2';
        }
    }, 1000);
}

// ── Question Navigation ──
function showQuestion(num) {
    document.querySelectorAll('.question-card').forEach(el => el.classList.add('d-none'));
    const cards = document.querySelectorAll('.question-card');
    if (cards[num - 1]) cards[num - 1].classList.remove('d-none');

    // Update nav buttons
    document.querySelectorAll('.q-nav-btn').forEach(btn => btn.classList.remove('active'));
    const navBtn = document.getElementById(`qnav-${num}`);
    if (navBtn) navBtn.classList.add('active');

    // Update current Q display
    document.getElementById('currentQ').textContent = num;

    // Show/hide prev/next/submit
    document.getElementById('btnPrev').disabled = (num <= 1);

    if (num >= totalQuestions) {
        document.getElementById('btnNext').classList.add('d-none');
        document.getElementById('btnSubmit').classList.remove('d-none');
    } else {
        document.getElementById('btnNext').classList.remove('d-none');
        document.getElementById('btnSubmit').classList.add('d-none');
    }

    currentQuestion = num;
}

function nextQuestion() {
    if (currentQuestion < totalQuestions) {
        showQuestion(currentQuestion + 1);
    }
}

function prevQuestion() {
    if (currentQuestion > 1) {
        showQuestion(currentQuestion - 1);
    }
}

function goToQuestion(num) {
    showQuestion(num);
}

// ── Answer Saving ──
function saveAnswer(questionId, option) {
    fetch('/api/exam/save-answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            exam_id: examId,
            question_id: questionId,
            selected_option: option
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            answeredQuestions.add(questionId);
            // Mark as answered in navigator
            const navBtn = document.querySelector(`.q-nav-btn[data-question-id="${questionId}"]`);
            if (navBtn && !navBtn.classList.contains('active')) {
                navBtn.classList.add('answered');
            }
        }
    })
    .catch(err => console.error('Save answer error:', err));
}

// ── Exam Submission ──
function submitExam() {
    if (!confirm('Are you sure you want to submit your exam? This action cannot be undone.')) return;
    doSubmitExam();
}

function autoSubmitExam() {
    alert('Time is up! Your exam will be submitted automatically.');
    doSubmitExam();
}

function doSubmitExam() {
    isExamActive = false;
    clearInterval(timerInterval);
    clearInterval(analysisInterval);

    // Exit fullscreen
    if (document.exitFullscreen) document.exitFullscreen().catch(() => {});

    // Stop camera
    if (proctoringStream) {
        proctoringStream.getTracks().forEach(track => track.stop());
    }

    fetch('/api/exam/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ exam_id: examId })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            const result = data.result;
            const passed = result.is_passed;
            const icon = passed ? '🎉' : '😔';
            const color = passed ? 'success' : 'danger';
            const text = passed ? 'PASSED' : 'FAILED';

            document.getElementById('resultContent').innerHTML = `
                <div class="display-1 mb-3">${icon}</div>
                <h3 class="fw-bold text-${color}">Exam ${text}!</h3>
                <div class="my-4">
                    <h1 class="display-3 fw-bold text-${color}">${result.total_score} / ${result.total_marks}</h1>
                    <p class="text-muted">Score: ${result.percentage}%</p>
                </div>
                <div class="row text-center g-3 mb-3">
                    <div class="col-4">
                        <div class="p-2 rounded-3" style="background: rgba(255,255,255,0.05);">
                            <h5 class="mb-0">${result.answered_count}</h5>
                            <small class="text-muted">Answered</small>
                        </div>
                    </div>
                    <div class="col-4">
                        <div class="p-2 rounded-3" style="background: rgba(255,255,255,0.05);">
                            <h5 class="mb-0">${result.correct_count}</h5>
                            <small class="text-muted">Correct</small>
                        </div>
                    </div>
                    <div class="col-4">
                        <div class="p-2 rounded-3" style="background: rgba(255,255,255,0.05);">
                            <h5 class="mb-0">${warningCount}</h5>
                            <small class="text-muted">Warnings</small>
                        </div>
                    </div>
                </div>
            `;

            const modal = new bootstrap.Modal(document.getElementById('resultModal'));
            modal.show();
        }
    })
    .catch(err => {
        alert('Exam submission failed. Please contact the administrator.');
        window.location.href = '/student/dashboard';
    });
}

// ── Exam Termination ──
function terminateExam() {
    isExamActive = false;
    clearInterval(timerInterval);
    clearInterval(analysisInterval);

    if (document.exitFullscreen) document.exitFullscreen().catch(() => {});
    if (proctoringStream) {
        proctoringStream.getTracks().forEach(track => track.stop());
    }

    fetch('/api/exam/terminate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ exam_id: examId })
    })
    .then(res => res.json())
    .then(() => {
        const modal = new bootstrap.Modal(document.getElementById('terminationModal'));
        modal.show();
    })
    .catch(() => {
        alert('Exam terminated. Returning to dashboard.');
        window.location.href = '/student/dashboard';
    });
}
