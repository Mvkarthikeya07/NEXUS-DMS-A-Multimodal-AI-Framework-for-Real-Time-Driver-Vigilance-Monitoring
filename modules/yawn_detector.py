"""Yawn detection module using Mouth Aspect Ratio (MAR)."""

import logging
from typing import List

import numpy as np

logger = logging.getLogger(__name__)


class YawnDetector:
    """Detects yawning by monitoring Mouth Aspect Ratio (MAR).
    
    A yawn is registered when MAR exceeds the threshold, with
    debounce logic to prevent counting one yawn multiple times.
    """

    def __init__(self, mar_threshold: float = 0.65):
        self.mar_threshold = mar_threshold
        self._yawn_count: int = 0
        self._is_yawning: bool = False
        self._was_yawning: bool = False  # For edge detection

    @staticmethod
    def mouth_aspect_ratio(mouth: List[np.ndarray]) -> float:
        """Calculate the Mouth Aspect Ratio (MAR).
        
        MAR = (|p2-p8| + |p3-p7| + |p4-p6|) / (3 * |p1-p5|)
        where p1-p8 are the 8 mouth landmark points.
        
        Args:
            mouth: List of 8 landmark points as numpy arrays.
            
        Returns:
            MAR value. Returns 0.0 if calculation is invalid.
        """
        if len(mouth) < 8:
            return 0.0
        A = np.linalg.norm(mouth[1] - mouth[7])
        B = np.linalg.norm(mouth[2] - mouth[6])
        C = np.linalg.norm(mouth[3] - mouth[5])
        D = np.linalg.norm(mouth[0] - mouth[4])
        if D < 1e-6:
            return 0.0
        return (A + B + C) / (3.0 * D)

    def update(self, mar: float) -> bool:
        """Update yawn detection state with new MAR value.
        
        Args:
            mar: Current MAR value.
            
        Returns:
            True if a NEW yawn was just detected (rising edge), False otherwise.
        """
        self._is_yawning = mar > self.mar_threshold
        new_yawn = self._is_yawning and not self._was_yawning
        if new_yawn:
            self._yawn_count += 1
            logger.info("Yawn detected (count: %d)", self._yawn_count)
        self._was_yawning = self._is_yawning
        return new_yawn

    def reset(self) -> None:
        """Reset yawn detection state."""
        self._yawn_count = 0
        self._is_yawning = False
        self._was_yawning = False

    @property
    def is_yawning(self) -> bool:
        return self._is_yawning

    @property
    def yawn_count(self) -> int:
        return self._yawn_count