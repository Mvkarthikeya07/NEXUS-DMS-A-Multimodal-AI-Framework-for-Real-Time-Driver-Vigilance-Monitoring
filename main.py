"""NEXUS-DMS — Real-time Driver Monitoring System.

Production-grade entry point that orchestrates all detection modules
and manages the main video processing loop.

Usage:
    python main.py
    
Press ESC to exit.
"""

import logging
import re
import signal
import sys
import time
import tkinter as tk
from typing import Optional

import cv2
import numpy as np

from config import Config
from logger import setup_logging, EventLogger
from modules.camera import Camera
from modules.face_analyzer import FaceAnalyzer, FaceData
from modules.drowsiness import DrowsinessDetector
from modules.yawn_detector import YawnDetector
from modules.distraction_detector import DistractionDetector, HeadDirection
from modules.phone_detector import PhoneDetector
from modules.alert_manager import AlertManager

logger = logging.getLogger(__name__)


class SafeDriveApp:
    """Main application class for NEXUS-DMS driver monitoring system.
    
    Coordinates camera input, face analysis, detection modules, 
    alert management, and HUD rendering in a clean main loop.
    """

    # Driver status constants
    STATUS_ATTENTIVE = "ATTENTIVE"
    STATUS_NO_FACE = "NO FACE"
    STATUS_DROWSY = "DROWSY"
    STATUS_DISTRACTED = "DISTRACTED"
    STATUS_PHONE = "PHONE DETECTED"

    # HUD Colors (BGR)
    COLOR_GREEN = (0, 255, 0)
    COLOR_RED = (0, 0, 255)
    COLOR_YELLOW = (0, 255, 255)
    COLOR_CYAN = (255, 255, 0)
    COLOR_WHITE = (255, 255, 255)
    COLOR_DARK_BG = (20, 20, 20)
    COLOR_ORANGE = (0, 165, 255)

    WINDOW_NAME = "NEXUS-DMS"

    def __init__(self, registered_phone: str = ""):
        """Initialize all components.
        
        Args:
            registered_phone: Phone number entered by the driver at startup.
                              Overrides EMERGENCY_CONTACT from config if provided.
        """
        Config.ensure_directories()

        # Event logger
        self.event_logger = EventLogger(str(Config.LOG_FILE))

        # Camera
        self.camera = Camera(
            index=Config.CAMERA_INDEX,
            width=Config.CAMERA_WIDTH,
            height=Config.CAMERA_HEIGHT,
        )

        # Face analysis
        self.face_analyzer = FaceAnalyzer(
            max_num_faces=Config.MAX_NUM_FACES,
            min_detection_confidence=Config.MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=Config.MIN_TRACKING_CONFIDENCE,
            refine_landmarks=Config.REFINE_LANDMARKS,
            left_eye_indices=Config.LEFT_EYE_INDICES,
            right_eye_indices=Config.RIGHT_EYE_INDICES,
            mouth_indices=Config.MOUTH_INDICES,
            nose_tip_index=Config.NOSE_TIP_INDEX,
            left_face_index=Config.LEFT_FACE_INDEX,
            right_face_index=Config.RIGHT_FACE_INDEX,
            forehead_index=Config.FOREHEAD_INDEX,
            chin_index=Config.CHIN_INDEX,
        )

        # Detection modules
        self.drowsiness = DrowsinessDetector(
            ear_threshold=Config.EAR_THRESHOLD,
            drowsy_frames=Config.DROWSY_FRAMES,
        )
        self.yawn_detector = YawnDetector(mar_threshold=Config.MAR_THRESHOLD)
        self.distraction = DistractionDetector(
            horizontal_threshold=Config.HEAD_TURN_THRESHOLD,
            alert_delay=Config.DISTRACTION_ALERT_DELAY,
        )
        self.phone_detector = PhoneDetector(
            model_path=str(Config.MODEL_PATH),
            confidence=Config.PHONE_CONFIDENCE,
        )

        # Resolve emergency contact: registered phone takes priority over config
        emergency_contact = registered_phone if registered_phone else Config.EMERGENCY_CONTACT
        if registered_phone:
            logger.info("Registered emergency contact: %s", registered_phone)

        # Alert manager
        self.alert_manager = AlertManager(
            alarm_path=str(Config.ALARM_FILE),
            screenshot_dir=str(Config.SCREENSHOT_DIR),
            voice_delay=Config.VOICE_ALERT_DELAY,
            buzzer_delay=Config.BUZZER_ALERT_DELAY,
            emergency_delay=Config.EMERGENCY_ALERT_DELAY,
            twilio_sid=Config.TWILIO_ACCOUNT_SID,
            twilio_token=Config.TWILIO_AUTH_TOKEN,
            twilio_from=Config.TWILIO_FROM_NUMBER,
            emergency_contact=emergency_contact,
        )

        # Runtime state
        self._running = False
        self._fps_time = time.time()
        self._fps = 0.0
        self._frame_count = 0
        self._status = self.STATUS_NO_FACE

        logger.info("NEXUS-DMS initialized successfully")

    def _log_event(self, event: str) -> None:
        """Callback for alert manager to log events."""
        self.event_logger.log(event)

    def _process_frame(self, frame: np.ndarray) -> np.ndarray:
        """Process a single video frame through all detection pipelines.
        
        Args:
            frame: BGR video frame from camera.
            
        Returns:
            Annotated frame with HUD overlay.
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self._status = self.STATUS_NO_FACE
        ear = 0.0
        mar = 0.0
        direction = HeadDirection.NO_FACE

        # ── Face Analysis ──
        face_data: FaceData = self.face_analyzer.analyze(rgb)

        if face_data.detected:
            self._status = self.STATUS_ATTENTIVE

            # EAR & Drowsiness
            ear = self.drowsiness.compute_ear(face_data.left_eye, face_data.right_eye)
            is_drowsy = self.drowsiness.update(ear)

            # MAR & Yawn
            mar = self.yawn_detector.mouth_aspect_ratio(face_data.mouth)
            new_yawn = self.yawn_detector.update(mar)
            if new_yawn:
                self.alert_manager.capture_screenshot(frame, "yawn")
                self._log_event("YAWN_DETECTED")

            # Head Pose & Distraction
            direction = self.distraction.compute_direction(
                nose_x=face_data.nose_x,
                face_center_x=face_data.face_center_x,
                nose_y=face_data.nose_y,
                forehead_y=face_data.forehead_y,
                chin_y=face_data.chin_y,
            )
            distraction_alert = self.distraction.update(direction)

            # ── Drowsiness Alert Pipeline ──
            if is_drowsy:
                self._status = self.STATUS_DROWSY
                self.alert_manager.handle_drowsy(frame, log_callback=self._log_event)
            else:
                self.alert_manager.reset_drowsy()

            # ── Distraction Alert Pipeline ──
            if self.distraction.is_distracted:
                self._status = self.STATUS_DISTRACTED
                if distraction_alert:
                    self.alert_manager.handle_distraction(
                        frame, direction.value, log_callback=self._log_event
                    )
            else:
                self.alert_manager.reset_distraction()

            # Draw face landmarks
            self._draw_landmarks(frame, face_data)

        # ── Phone Detection (independent of face) ──
        # Pass the face bounding box so the detector can suppress
        # false positives caused by yawning mouth or hands near the face.
        face_box = getattr(face_data, 'face_box', None) if face_data.detected else None
        is_yawning = mar > self.yawn_detector.mar_threshold if face_data.detected else False

        phone_detected, phone_boxes = self.phone_detector.detect(frame, face_box=face_box)

        # Suppress phone alert entirely while the driver is yawning —
        # an open mouth can confuse the model into detecting a phone.
        if phone_detected and not is_yawning:
            self._status = self.STATUS_PHONE
            self.phone_detector.draw_detections(frame, phone_boxes)
            self.alert_manager.handle_phone(
                frame,
                phone_sms_delay=Config.PHONE_SMS_DELAY,
                log_callback=self._log_event,
            )
        else:
            self.alert_manager.reset_phone()

        # ── HUD Overlay ──
        self._draw_hud(frame, ear, mar, direction)

        return frame

    def _draw_landmarks(self, frame: np.ndarray, face_data: FaceData) -> None:
        """Draw eye and mouth landmark overlays on the frame."""
        for points in (face_data.left_eye, face_data.right_eye, face_data.mouth):
            if len(points) > 0:
                pts = np.array(points, dtype=np.int32)
                cv2.polylines(frame, [pts], True, self.COLOR_GREEN, 1)
                for pt in points:
                    cv2.circle(frame, tuple(pt.astype(int)), 2, self.COLOR_GREEN, -1)

    def _draw_hud(
        self,
        frame: np.ndarray,
        ear: float,
        mar: float,
        direction: HeadDirection,
    ) -> None:
        """Draw the heads-up display panel on the frame."""
        h, w = frame.shape[:2]

        # Background panel
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (320, 290), self.COLOR_DARK_BG, -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        # Title
        cv2.putText(
            frame, "NEXUS-DMS", (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX, 0.75, self.COLOR_WHITE, 2,
        )

        # Separator line
        cv2.line(frame, (20, 52), (300, 52), (60, 60, 60), 1)

        # Status
        status_color = {
            self.STATUS_ATTENTIVE: self.COLOR_GREEN,
            self.STATUS_DROWSY: self.COLOR_RED,
            self.STATUS_DISTRACTED: self.COLOR_ORANGE,
            self.STATUS_PHONE: self.COLOR_RED,
            self.STATUS_NO_FACE: self.COLOR_YELLOW,
        }.get(self._status, self.COLOR_WHITE)

        cv2.putText(
            frame, f"Status: {self._status}", (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2,
        )

        # Metrics
        cv2.putText(
            frame, f"EAR: {ear:.3f}", (20, 110),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, self.COLOR_YELLOW, 1,
        )
        cv2.putText(
            frame, f"MAR: {mar:.3f}", (20, 135),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, self.COLOR_CYAN, 1,
        )
        cv2.putText(
            frame, f"Head: {direction.value}", (20, 160),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, self.COLOR_WHITE, 1,
        )
        cv2.putText(
            frame, f"Yawns: {self.yawn_detector.yawn_count}", (20, 185),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, self.COLOR_WHITE, 1,
        )

        # Drowsy timer
        drowsy_time = self.alert_manager.drowsy_elapsed
        timer_color = self.COLOR_RED if drowsy_time > 0 else self.COLOR_WHITE
        cv2.putText(
            frame, f"Drowsy Timer: {drowsy_time:.1f}s", (20, 215),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, timer_color, 1,
        )

        # Alert indicators
        voice_indicator = "ON" if self.alert_manager._drowsy_voice_sent else "OFF"
        buzzer_indicator = "ON" if self.alert_manager._drowsy_buzzer_started else "OFF"
        cv2.putText(
            frame, f"Voice: {voice_indicator}  Buzzer: {buzzer_indicator}", (20, 240),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45, self.COLOR_WHITE, 1,
        )

        # FPS
        cv2.putText(
            frame, f"FPS: {self._fps:.0f}", (20, 270),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 100, 100), 1,
        )

        # Status banner for alerts
        if self._status == self.STATUS_DROWSY:
            self._draw_alert_banner(frame, "DROWSY ALERT!", self.COLOR_RED)
        elif self._status == self.STATUS_PHONE:
            self._draw_alert_banner(frame, "PHONE DETECTED!", self.COLOR_RED)
        elif self._status == self.STATUS_DISTRACTED:
            self._draw_alert_banner(frame, "DISTRACTION!", self.COLOR_ORANGE)

    def _draw_alert_banner(
        self, frame: np.ndarray, text: str, color: tuple
    ) -> None:
        """Draw a flashing alert banner at the top of the frame."""
        h, w = frame.shape[:2]
        # Blinking effect (based on time)
        if int(time.time() * 3) % 2 == 0:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, h - 60), (w, h), color, -1)
            cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 3)[0]
            text_x = (w - text_size[0]) // 2
            cv2.putText(
                frame, text, (text_x, h - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, self.COLOR_WHITE, 3,
            )

    def _update_fps(self) -> None:
        """Calculate and update FPS counter."""
        self._frame_count += 1
        elapsed = time.time() - self._fps_time
        if elapsed >= 1.0:
            self._fps = self._frame_count / elapsed
            self._frame_count = 0
            self._fps_time = time.time()

    def run(self) -> None:
        """Start the main application loop."""
        if not self.camera.open():
            logger.error("Cannot open camera. Exiting.")
            sys.exit(1)

        self._running = True
        logger.info("NEXUS-DMS is running. Press ESC to exit.")

        try:
            while self._running:
                success, frame = self.camera.read()
                if not success:
                    logger.warning("Failed to read frame, retrying...")
                    continue

                # Process frame through all pipelines
                annotated = self._process_frame(frame)

                # Update FPS
                self._update_fps()

                # Display
                cv2.imshow(self.WINDOW_NAME, annotated)

                # Check for exit (ESC key)
                if cv2.waitKey(1) & 0xFF == 27:
                    logger.info("ESC pressed. Shutting down...")
                    break

        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received. Shutting down...")
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        """Gracefully shut down all resources."""
        self._running = False
        self.camera.release()
        self.face_analyzer.close()
        self.alert_manager.cleanup()
        cv2.destroyAllWindows()
        logger.info("NEXUS-DMS shut down successfully")


def _prompt_phone_number() -> str:
    """Show a Tkinter dialog asking the driver to register their phone number.
    
    Returns:
        Validated phone number string (E.164 format), or empty string if skipped.
    """
    result: dict = {"phone": ""}

    root = tk.Tk()
    root.title("NEXUS-DMS — Register Contact")
    root.resizable(False, False)
    root.configure(bg="#0d0d0d")

    # Center window on screen
    window_w, window_h = 480, 320
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    x = (screen_w - window_w) // 2
    y = (screen_h - window_h) // 2
    root.geometry(f"{window_w}x{window_h}+{x}+{y}")

    # ── Styles ──────────────────────────────────────────────────
    BG        = "#0d0d0d"
    CARD_BG   = "#1a1a2e"
    ACCENT    = "#e94560"
    TEXT_MAIN = "#eaeaea"
    TEXT_DIM  = "#888888"
    ENTRY_BG  = "#16213e"

    # Card frame
    card = tk.Frame(root, bg=CARD_BG, bd=0, highlightthickness=2,
                    highlightbackground=ACCENT)
    card.place(relx=0.5, rely=0.5, anchor="center", width=440, height=280)

    # Logo / title
    tk.Label(card, text="🚗  SAFE DRIVE AI", font=("Segoe UI", 16, "bold"),
             fg=ACCENT, bg=CARD_BG).pack(pady=(22, 4))
    tk.Label(card, text="Driver Monitoring System", font=("Segoe UI", 9),
             fg=TEXT_DIM, bg=CARD_BG).pack()

    tk.Frame(card, height=1, bg=ACCENT).pack(fill="x", padx=20, pady=10)

    tk.Label(card,
             text="Enter your phone number to receive safety alerts:",
             font=("Segoe UI", 10), fg=TEXT_MAIN, bg=CARD_BG,
             wraplength=380).pack(padx=20)

    # Phone entry
    entry_frame = tk.Frame(card, bg=ENTRY_BG, bd=0,
                           highlightthickness=1, highlightbackground="#333")
    entry_frame.pack(padx=30, pady=10, fill="x")

    phone_var = tk.StringVar()
    entry = tk.Entry(entry_frame, textvariable=phone_var,
                     font=("Consolas", 14), bg=ENTRY_BG, fg=TEXT_MAIN,
                     insertbackground=ACCENT, bd=0, relief="flat",
                     justify="center")
    entry.pack(ipady=10, padx=10, fill="x")
    entry.insert(0, "+91")
    entry.focus()

    error_lbl = tk.Label(card, text="", font=("Segoe UI", 9),
                         fg=ACCENT, bg=CARD_BG)
    error_lbl.pack()

    def _validate_and_start():
        raw = phone_var.get().strip()
        # Allow digits, +, spaces, dashes, parentheses
        digits_only = re.sub(r"[^\d]", "", raw)
        if len(digits_only) < 7 or len(digits_only) > 15:
            error_lbl.config(text="⚠  Please enter a valid phone number (7–15 digits).")
            return
        # Normalize to E.164: if starts with +, keep; else prepend +
        if raw.startswith("+"):
            normalized = "+" + digits_only
        else:
            normalized = "+" + digits_only
        result["phone"] = normalized
        root.destroy()

    def _skip():
        result["phone"] = ""
        root.destroy()

    # Buttons row
    btn_frame = tk.Frame(card, bg=CARD_BG)
    btn_frame.pack(pady=(0, 16))

    tk.Button(btn_frame, text="  Start Monitoring  ",
              font=("Segoe UI", 10, "bold"),
              bg=ACCENT, fg="white", activebackground="#c73652",
              activeforeground="white", bd=0, padx=12, pady=8,
              cursor="hand2", command=_validate_and_start).pack(side="left", padx=8)

    tk.Button(btn_frame, text="Skip",
              font=("Segoe UI", 10),
              bg="#2a2a3e", fg=TEXT_DIM, activebackground="#333",
              activeforeground=TEXT_MAIN, bd=0, padx=12, pady=8,
              cursor="hand2", command=_skip).pack(side="left", padx=8)

    # Allow Enter key to submit
    root.bind("<Return>", lambda _e: _validate_and_start())
    root.bind("<Escape>", lambda _e: _skip())

    root.mainloop()
    return result["phone"]


def main():
    """Application entry point."""
    setup_logging(logging.INFO)
    logger.info("=" * 60)
    logger.info("  SAFE DRIVE AI — Driver Monitoring System")
    logger.info("=" * 60)

    # ── Step 1: Prompt driver for their phone number ────────────
    registered_phone = _prompt_phone_number()
    if registered_phone:
        logger.info("Phone registered for alerts: %s", registered_phone)
    else:
        logger.info("No phone number registered. SMS alerts will use config fallback.")

    # ── Step 2: Launch the monitoring app ──────────────────────
    app = SafeDriveApp(registered_phone=registered_phone)

    # Handle graceful shutdown signals
    def signal_handler(sig, _frame):
        logger.info("Signal %s received, shutting down...", sig)
        app.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, signal_handler)

    app.run()


if __name__ == "__main__":
    main()
