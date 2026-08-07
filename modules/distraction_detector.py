"""Distraction detection module using head pose estimation."""

import logging
import time
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class HeadDirection(Enum):
    """Possible head directions."""
    CENTER = "CENTER"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    UP = "UP"
    DOWN = "DOWN"
    NO_FACE = "NO FACE"


class DistractionDetector:
    """Detects driver distraction through head pose estimation.
    
    Uses nose position relative to face center to determine head direction.
    Flags distraction when the driver looks away for a sustained period.
    """

    def __init__(
        self,
        horizontal_threshold: float = 0.03,
        vertical_up_threshold: float = 0.42,
        vertical_down_threshold: float = 0.58,
        alert_delay: float = 3.0,
    ):
        self.horizontal_threshold = horizontal_threshold
        self.vertical_up_threshold = vertical_up_threshold
        self.vertical_down_threshold = vertical_down_threshold
        self.alert_delay = alert_delay

        self._direction: HeadDirection = HeadDirection.NO_FACE
        self._distraction_start: Optional[float] = None
        self._alert_sent: bool = False

    def compute_direction(
        self,
        nose_x: float,
        face_center_x: float,
        nose_y: float = 0.0,
        forehead_y: float = 0.0,
        chin_y: float = 0.0,
    ) -> HeadDirection:
        """Compute head direction from facial landmarks.
        
        Args:
            nose_x: Normalized nose tip X coordinate.
            face_center_x: Normalized face center X coordinate.
            nose_y: Nose Y in pixels (for vertical detection).
            forehead_y: Forehead Y in pixels.
            chin_y: Chin Y in pixels.
            
        Returns:
            HeadDirection enum value.
        """
        # Horizontal check
        if nose_x < face_center_x - self.horizontal_threshold:
            self._direction = HeadDirection.LEFT
        elif nose_x > face_center_x + self.horizontal_threshold:
            self._direction = HeadDirection.RIGHT
        else:
            # Vertical check (only if face height is valid)
            face_height = chin_y - forehead_y
            if face_height > 1e-6:
                nose_ratio = (nose_y - forehead_y) / face_height
                if nose_ratio < self.vertical_up_threshold:
                    self._direction = HeadDirection.UP
                elif nose_ratio > self.vertical_down_threshold:
                    self._direction = HeadDirection.DOWN
                else:
                    self._direction = HeadDirection.CENTER
            else:
                self._direction = HeadDirection.CENTER
        return self._direction

    def update(self, direction: HeadDirection) -> bool:
        """Update distraction state.
        
        Args:
            direction: Current head direction.
            
        Returns:
            True if distraction alert should fire (first time only after delay).
        """
        is_distracted = direction not in (HeadDirection.CENTER, HeadDirection.NO_FACE)

        if is_distracted:
            if self._distraction_start is None:
                self._distraction_start = time.time()
            elapsed = time.time() - self._distraction_start
            if elapsed >= self.alert_delay and not self._alert_sent:
                self._alert_sent = True
                logger.warning("Distraction detected: %s for %.1fs", direction.value, elapsed)
                return True
        else:
            self._distraction_start = None
            self._alert_sent = False

        return False

    def reset(self) -> None:
        """Reset distraction state."""
        self._direction = HeadDirection.NO_FACE
        self._distraction_start = None
        self._alert_sent = False

    @property
    def direction(self) -> HeadDirection:
        return self._direction

    @property
    def is_distracted(self) -> bool:
        return self._direction not in (HeadDirection.CENTER, HeadDirection.NO_FACE)

    @property
    def distraction_duration(self) -> float:
        if self._distraction_start is None:
            return 0.0
        return time.time() - self._distraction_start
