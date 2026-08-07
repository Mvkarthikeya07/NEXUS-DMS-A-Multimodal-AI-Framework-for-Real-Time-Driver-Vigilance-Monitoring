"""Face analysis module using MediaPipe Face Mesh."""

import logging
from dataclasses import dataclass, field
from typing import List, Optional

import mediapipe as mp
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class FaceData:
    """Structured container for face analysis results."""
    detected: bool = False
    left_eye: List[np.ndarray] = field(default_factory=list)
    right_eye: List[np.ndarray] = field(default_factory=list)
    mouth: List[np.ndarray] = field(default_factory=list)
    nose_x: float = 0.0
    face_center_x: float = 0.0
    nose_y: float = 0.0
    forehead_y: float = 0.0
    chin_y: float = 0.0
    frame_height: int = 0
    frame_width: int = 0


class FaceAnalyzer:
    """Analyzes faces using MediaPipe Face Mesh to extract landmarks."""

    def __init__(
        self,
        max_num_faces: int = 1,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        refine_landmarks: bool = True,
        left_eye_indices: List[int] = None,
        right_eye_indices: List[int] = None,
        mouth_indices: List[int] = None,
        nose_tip_index: int = 1,
        left_face_index: int = 234,
        right_face_index: int = 454,
        forehead_index: int = 10,
        chin_index: int = 152,
    ):
        self._left_eye_idx = left_eye_indices or [33, 160, 158, 133, 153, 144]
        self._right_eye_idx = right_eye_indices or [362, 385, 387, 263, 373, 380]
        self._mouth_idx = mouth_indices or [78, 81, 13, 311, 308, 402, 14, 178]
        self._nose_tip_idx = nose_tip_index
        self._left_face_idx = left_face_index
        self._right_face_idx = right_face_index
        self._forehead_idx = forehead_index
        self._chin_idx = chin_index

        self._face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=max_num_faces,
            refine_landmarks=refine_landmarks,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        logger.info("FaceAnalyzer initialized")

    def analyze(self, frame_rgb: np.ndarray) -> FaceData:
        """Analyze a single RGB frame and extract face landmarks.
        
        Args:
            frame_rgb: RGB image as numpy array (H, W, 3).
            
        Returns:
            FaceData with extracted landmarks, or FaceData(detected=False) if no face.
        """
        h, w, _ = frame_rgb.shape
        results = self._face_mesh.process(frame_rgb)

        if not results.multi_face_landmarks:
            return FaceData(detected=False, frame_height=h, frame_width=w)

        face = results.multi_face_landmarks[0]
        data = FaceData(detected=True, frame_height=h, frame_width=w)

        # Extract eye landmarks
        for idx in self._left_eye_idx:
            lm = face.landmark[idx]
            data.left_eye.append(np.array([lm.x * w, lm.y * h]))

        for idx in self._right_eye_idx:
            lm = face.landmark[idx]
            data.right_eye.append(np.array([lm.x * w, lm.y * h]))

        for idx in self._mouth_idx:
            lm = face.landmark[idx]
            data.mouth.append(np.array([lm.x * w, lm.y * h]))

        # Head pose landmarks
        nose = face.landmark[self._nose_tip_idx]
        left_face = face.landmark[self._left_face_idx]
        right_face = face.landmark[self._right_face_idx]
        forehead = face.landmark[self._forehead_idx]
        chin = face.landmark[self._chin_idx]

        data.nose_x = nose.x
        data.nose_y = nose.y * h
        data.face_center_x = (left_face.x + right_face.x) / 2.0
        data.forehead_y = forehead.y * h
        data.chin_y = chin.y * h

        return data

    def close(self) -> None:
        """Release MediaPipe resources."""
        self._face_mesh.close()
        logger.info("FaceAnalyzer closed")
