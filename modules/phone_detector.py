"""Mobile phone detection module using YOLOv8."""

import logging
from typing import List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class PhoneDetector:
    """Detects mobile phone usage using YOLOv8 object detection.

    Uses the COCO dataset's 'cell phone' class (index 67) for detection.

    False-positive filters applied:
    - Confidence threshold (default 0.50)
    - Face overlap guard: rejects boxes that overlap significantly with
      the driver's face region (prevents open mouth / hand near face
      being classified as a phone)
    - Aspect ratio guard: phones are portrait (height > width); wide
      boxes are likely hands or mouth regions
    - Minimum size guard: very small detections are noise
    """

    CELL_PHONE_CLASS = 67  # COCO class index for cell phone

    # Overlap ratio above which a detection is considered face-region noise
    FACE_OVERLAP_THRESHOLD = 0.35

    def __init__(self, model_path: str = "yolov8n.pt", confidence: float = 0.50):
        self.confidence = confidence
        self._model = None
        self._model_path = model_path
        self._load_model()

    def _load_model(self) -> None:
        """Load the YOLO model, downloading automatically if not found."""
        try:
            import os
            from ultralytics import YOLO

            if os.path.exists(self._model_path):
                self._model = YOLO(self._model_path)
                logger.info("YOLO model loaded from %s", self._model_path)
            else:
                model_name = os.path.basename(self._model_path)
                logger.info("Model not found — downloading %s...", model_name)
                self._model = YOLO(model_name)
                logger.info("YOLO model %s downloaded and loaded", model_name)
        except Exception as e:
            logger.error("Failed to load YOLO model: %s", e)
            self._model = None

    @staticmethod
    def _iou(boxA: Tuple[int, int, int, int], boxB: Tuple[int, int, int, int]) -> float:
        """Compute intersection-over-union between two (x1,y1,x2,y2) boxes."""
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        inter = max(0, xB - xA) * max(0, yB - yA)
        if inter == 0:
            return 0.0
        areaA = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        areaB = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        return inter / float(areaA + areaB - inter)

    def _is_false_positive(
        self,
        x1: int, y1: int, x2: int, y2: int,
        face_box: Optional[Tuple[int, int, int, int]],
        frame_h: int, frame_w: int,
    ) -> bool:
        """Return True if this detection is likely a false positive.

        Checks:
        1. Face overlap — if the detected box overlaps the face region
           by more than FACE_OVERLAP_THRESHOLD it is likely an open
           mouth, yawning, or hand held near the face.
        2. Aspect ratio — a real phone held in-hand is taller than wide
           (portrait). If the box is very wide relative to its height
           it is likely a hand, mouth, or background object.
        3. Minimum area — boxes smaller than 0.2% of the frame are noise.
        """
        w = x2 - x1
        h = y2 - y1

        # Guard: minimum area (< 0.2 % of frame)
        min_area = 0.002 * frame_h * frame_w
        if w * h < min_area:
            return True

        # Guard: aspect ratio — reject very wide boxes (width > 2× height)
        if w > 2.0 * h:
            return True

        # Guard: face overlap
        if face_box is not None:
            overlap = self._iou((x1, y1, x2, y2), face_box)
            if overlap > self.FACE_OVERLAP_THRESHOLD:
                logger.debug(
                    "Phone detection suppressed — face overlap %.2f > %.2f",
                    overlap, self.FACE_OVERLAP_THRESHOLD,
                )
                return True

        return False

    def detect(
        self,
        frame: np.ndarray,
        face_box: Optional[Tuple[int, int, int, int]] = None,
    ) -> Tuple[bool, List[Tuple[int, int, int, int, float]]]:
        """Detect phones in a frame with false-positive filtering.

        Args:
            frame:    BGR image as numpy array.
            face_box: Optional (x1, y1, x2, y2) bounding box of the
                      driver's face, used to suppress face-region
                      false positives (yawning mouth, hands near face).

        Returns:
            Tuple of (phone_detected: bool,
                      detections: list of (x1, y1, x2, y2, conf)).
        """
        if self._model is None:
            return False, []

        h, w = frame.shape[:2]
        detections = []

        try:
            results = self._model(frame, verbose=False)
            for r in results:
                for box in r.boxes:
                    cls  = int(box.cls[0])
                    conf = float(box.conf[0])
                    if cls != self.CELL_PHONE_CLASS or conf < self.confidence:
                        continue
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    if not self._is_false_positive(x1, y1, x2, y2, face_box, h, w):
                        detections.append((x1, y1, x2, y2, conf))
        except Exception as e:
            logger.error("Phone detection error: %s", e)

        return len(detections) > 0, detections

    def draw_detections(
        self,
        frame: np.ndarray,
        detections: List[Tuple[int, int, int, int, float]],
    ) -> np.ndarray:
        """Draw phone detection bounding boxes on frame.

        Args:
            frame:      BGR image to annotate.
            detections: List of (x1, y1, x2, y2, confidence) tuples.

        Returns:
            Annotated frame.
        """
        for x1, y1, x2, y2, conf in detections:
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(
                frame, f"PHONE {conf:.0%}", (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2,
            )
        return frame
