/**
 * Face Capture JavaScript — handles camera, photo capture, and face registration.
 */

let cameraStream = null;
let capturedDataUrl = null;

function startCamera() {
    const video = document.getElementById('cameraFeed');
    navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: 'user' }
    })
    .then(stream => {
        cameraStream = stream;
        video.srcObject = stream;
        document.getElementById('btnStartCamera').style.display = 'none';
        document.getElementById('btnCapture').style.display = 'inline-block';
    })
    .catch(err => {
        alert('Camera access denied. Please allow camera access in your browser settings.\n\nError: ' + err.message);
    });
}

function capturePhoto() {
    const video = document.getElementById('cameraFeed');
    const canvas = document.getElementById('captureCanvas');
    const ctx = canvas.getContext('2d');

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);

    capturedDataUrl = canvas.toDataURL('image/jpeg', 0.92);

    // Show preview
    document.getElementById('capturedImage').src = capturedDataUrl;
    document.getElementById('capturedPreview').style.display = 'block';

    // Hide camera, show retake & save
    video.style.display = 'none';
    document.querySelector('.face-guide-overlay').style.display = 'none';
    document.getElementById('btnCapture').style.display = 'none';
    document.getElementById('btnRetake').style.display = 'inline-block';
    document.getElementById('btnSave').style.display = 'inline-block';
}

function retakePhoto() {
    const video = document.getElementById('cameraFeed');
    capturedDataUrl = null;

    // Show camera again
    video.style.display = 'block';
    document.querySelector('.face-guide-overlay').style.display = 'flex';
    document.getElementById('capturedPreview').style.display = 'none';
    document.getElementById('btnRetake').style.display = 'none';
    document.getElementById('btnSave').style.display = 'none';
    document.getElementById('btnCapture').style.display = 'inline-block';
}

function saveFace() {
    if (!capturedDataUrl) {
        alert('Please capture a photo first.');
        return;
    }

    // Show loading
    document.getElementById('btnRetake').style.display = 'none';
    document.getElementById('btnSave').style.display = 'none';
    document.getElementById('faceStatus').style.display = 'block';
    document.getElementById('statusText').textContent = 'Processing face encoding... Please wait.';

    fetch('/student/face-capture/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: capturedDataUrl })
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById('faceStatus').style.display = 'none';

        if (data.success) {
            // Success
            document.getElementById('statusText').textContent = '';
            document.getElementById('faceStatus').style.display = 'block';
            document.getElementById('faceStatus').innerHTML = `
                <i class="bi bi-check-circle-fill display-3 text-success"></i>
                <h5 class="text-success mt-2">${data.message}</h5>
                <a href="/student/dashboard" class="btn btn-accent rounded-pill px-4 mt-3">
                    <i class="bi bi-arrow-left me-2"></i>Back to Dashboard
                </a>
            `;

            // Stop camera
            if (cameraStream) {
                cameraStream.getTracks().forEach(track => track.stop());
            }
        } else {
            alert('Error: ' + data.message);
            document.getElementById('btnRetake').style.display = 'inline-block';
            document.getElementById('btnSave').style.display = 'inline-block';
        }
    })
    .catch(err => {
        document.getElementById('faceStatus').style.display = 'none';
        document.getElementById('btnRetake').style.display = 'inline-block';
        document.getElementById('btnSave').style.display = 'inline-block';
        alert('Failed to save face. Please try again.');
    });
}
