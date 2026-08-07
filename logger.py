"""Logging utilities for NEXUS-DMS."""

import csv
import logging
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger with console and file handlers."""
    log_format = "%(asctime)s [%(levelname)-8s] %(name)-25s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(),
        ],
    )


class EventLogger:
    """Thread-safe CSV event logger for NEXUS-DMS alerts.
    
    Logs events with timestamp to a CSV file for dashboard analysis.
    """

    def __init__(self, log_file: str = "logs/alerts.csv"):
        self._log_file = Path(log_file)
        self._log_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._logger = logging.getLogger("EventLogger")
        self._ensure_header()

    def _ensure_header(self) -> None:
        """Write CSV header if file doesn't exist or is empty."""
        if not self._log_file.exists() or self._log_file.stat().st_size == 0:
            with open(self._log_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "Time", "Event"])

    def log(self, event: str) -> None:
        """Log an event to the CSV file.
        
        Args:
            event: Event type string (e.g., 'DROWSY_WARNING', 'PHONE_DETECTED').
        """
        with self._lock:
            try:
                with open(self._log_file, "a", newline="") as f:
                    writer = csv.writer(f)
                    now = datetime.now()
                    writer.writerow([
                        now.strftime("%Y-%m-%d"),
                        now.strftime("%H:%M:%S"),
                        event,
                    ])
                self._logger.info("Event logged: %s", event)
            except Exception as e:
                self._logger.error("Failed to log event '%s': %s", event, e)

    def get_log_path(self) -> str:
        """Return the absolute path to the log file."""
        return str(self._log_file.resolve())