"""Drowsiness detection module using Eye Aspect Ratio (EAR)."""

import logging
from typing import List

import numpy as np

logger = logging.getLogger(__name__)


class DrowsinessDetector:
    """Detects drowsiness by monitoring Eye Aspect Ratio (EAR).
    
    The EAR drops significantly when eyes close. If EAR stays below
    the threshold for a sustained number of frames, drowsiness is flagged.
    """

    def __init__(self, ear_threshold: float = 0.25, drowsy_frames: int = 15):
        self.ear_threshold = ear_threshold
        self.drowsy_frames = drowsy_frames
        self._counter: int = 0
        self._is_drowsy: bool = False

    @staticmethod
    def eye_aspect_ratio(eye: List[np.ndarray]) -> float:
        """Calculate the Eye Aspect Ratio (EAR).
        
        EAR = (|p2-p6| + |p3-p5|) / (2 * |p1-p4|)
        where p1-p6 are the 6 eye landmark points.
        
        Args:
            eye: List of 6 landmark points as numpy arrays.
            
        Returns:
            EAR value. Returns 0.0 if calculation is invalid.
        """
        if len(eye) < 6:
            return 0.0
        A = np.linalg.norm(eye[1] - eye[5])
        B = np.linalg.norm(eye[2] - eye[4])
        C = np.linalg.norm(eye[0] - eye[3])
        if C < 1e-6:
            return 0.0
        return (A + B) / (2.0 * C)

    def compute_ear(
        self, left_eye: List[np.ndarray], right_eye: List[np.ndarray]
    ) -> float:
        """Compute average EAR from both eyes."""
        left_ear = self.eye_aspect_ratio(left_eye)
        right_ear = self.eye_aspect_ratio(right_eye)
        return (left_ear + right_ear) / 2.0

    def update(self, ear: float) -> bool:
        """Update drowsiness state with new EAR value.
        
        Args:
            ear: Current average EAR value.
            
        Returns:
            True if driver is drowsy, False otherwise.
        """
        if ear < self.ear_threshold:
            self._counter += 1
            if self._counter >= self.drowsy_frames:
                self._is_drowsy = True
        else:
            self._counter = 0
            self._is_drowsy = False
        return self._is_drowsy

    def reset(self) -> None:
        """Reset drowsiness detection state."""
        self._counter = 0
        self._is_drowsy = False

    @property
    def is_drowsy(self) -> bool:
        return self._is_drowsy

    @property
    def consecutive_frames(self) -> int:
        return self._counter