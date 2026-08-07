"""Camera management module for NEXUS-DMS."""

import cv2
import logging
import sys
from typing import Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class Camera:
    """Manages webcam capture with error handling and resource cleanup."""

    def __init__(self, index: int = 0, width: int = 640, height: int = 480):
        self.index = index
        self.width = width
        self.height = height
        self._cap: Optional[cv2.VideoCapture] = None

    def open(self) -> bool:
        """Open the camera. Returns True if successful."""
        backend = cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY
        self._cap = cv2.VideoCapture(self.index, backend)
        if not self._cap.isOpened():
            logger.error("Failed to open camera at index %d", self.index)
            return False
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        logger.info("Camera opened successfully (index=%d, %dx%d)", self.index, self.width, self.height)
        return True

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Read a frame from the camera. Returns (success, frame)."""
        if self._cap is None or not self._cap.isOpened():
            return False, None
        success, frame = self._cap.read()
        if success:
            frame = cv2.flip(frame, 1)  # Mirror for driver-facing camera
        return success, frame

    def release(self) -> None:
        """Release camera resources."""
        if self._cap is not None:
            self._cap.release()
            logger.info("Camera released")
        self._cap = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.release()
