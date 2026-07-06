"""
Mobile Phone Detection module using YOLOv3-tiny.
Falls back to a contour-based heuristic if YOLO weights are unavailable.
"""

import os
import cv2
import numpy as np


class PhoneDetector:
    """Detect mobile phones in video frames using YOLOv3-tiny or heuristic fallback."""

    # COCO class index for 'cell phone' is 67
    PHONE_CLASS_ID = 67
    PHONE_CLASS_NAME = "cell phone"

    def __init__(self, config_path=None, weights_path=None, classes_path=None, confidence_threshold=0.45):
        """Initialize phone detector.

        Args:
            config_path: Path to YOLO config file.
            weights_path: Path to YOLO weights file.
            classes_path: Path to COCO class names file.
            confidence_threshold: Minimum confidence for detection.
        """
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = 0.4
        self.net = None
        self.classes = []
        self.output_layers = []
        self.use_yolo = False

        # Try to load YOLO
        if config_path and weights_path and classes_path:
            if os.path.exists(config_path) and os.path.exists(weights_path) and os.path.exists(classes_path):
                try:
                    self.net = cv2.dnn.readNetFromDarknet(config_path, weights_path)
                    self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
                    self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

                    with open(classes_path, "r") as f:
                        self.classes = [line.strip() for line in f.readlines()]

                    layer_names = self.net.getLayerNames()
                    out_indices = self.net.getUnconnectedOutLayers()
                    if isinstance(out_indices[0], (list, np.ndarray)):
                        self.output_layers = [layer_names[i[0] - 1] for i in out_indices]
                    else:
                        self.output_layers = [layer_names[i - 1] for i in out_indices]

                    self.use_yolo = True
                except Exception:
                    self.use_yolo = False

    def detect_phone(self, frame):
        """Detect mobile phone in frame.

        Args:
            frame: BGR image as numpy array.

        Returns:
            Tuple of (phone_detected, confidence, bbox).
        """
        if self.use_yolo:
            return self._detect_yolo(frame)
        return self._detect_heuristic(frame)

    def _detect_yolo(self, frame):
        """Detect phone using YOLO.

        Args:
            frame: BGR image as numpy array.

        Returns:
            Tuple of (phone_detected, confidence, bbox).
        """
        h, w = frame.shape[:2]

        blob = cv2.dnn.blobFromImage(frame, 1/255.0, (416, 416), swapRB=True, crop=False)
        self.net.setInput(blob)
        outputs = self.net.forward(self.output_layers)

        boxes = []
        confidences = []

        for output in outputs:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = float(scores[class_id])

                if class_id == self.PHONE_CLASS_ID and confidence > self.confidence_threshold:
                    center_x = int(detection[0] * w)
                    center_y = int(detection[1] * h)
                    bw = int(detection[2] * w)
                    bh = int(detection[3] * h)

                    x = int(center_x - bw / 2)
                    y = int(center_y - bh / 2)

                    boxes.append([x, y, bw, bh])
                    confidences.append(confidence)

        if boxes:
            indices = cv2.dnn.NMSBoxes(boxes, confidences, self.confidence_threshold, self.nms_threshold)
            if len(indices) > 0:
                if isinstance(indices[0], (list, np.ndarray)):
                    idx = indices[0][0]
                else:
                    idx = indices[0]
                return True, confidences[idx], tuple(boxes[idx])

        return False, 0.0, None

    def _detect_heuristic(self, frame):
        """Heuristic-based phone detection using edge and shape analysis.
        This is a fallback when YOLO weights are not available.

        Args:
            frame: BGR image as numpy array.

        Returns:
            Tuple of (phone_detected, confidence, bbox).
        """
        h, w = frame.shape[:2]
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Detect dark rectangular objects (phone-like)
        # Phones typically appear as dark rectangular objects
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)

        # Dilate to connect edges
        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=2)

        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            # Phone-sized area (relative to frame)
            relative_area = area / (h * w)

            if 0.02 < relative_area < 0.25:
                rect = cv2.minAreaRect(contour)
                rect_w, rect_h = rect[1]

                if rect_w == 0 or rect_h == 0:
                    continue

                aspect_ratio = max(rect_w, rect_h) / min(rect_w, rect_h)

                # Phone-like aspect ratio (roughly 2:1)
                if 1.5 < aspect_ratio < 3.0:
                    x, y, bw, bh = cv2.boundingRect(contour)
                    confidence = min(0.6, relative_area * 5)
                    if confidence > self.confidence_threshold:
                        return True, float(confidence), (x, y, bw, bh)

        return False, 0.0, None
