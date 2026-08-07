"""Unified alert management for NEXUS-DMS."""

import logging
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class AlertManager:
    """Manages all alert types with staged escalation and cooldowns.

    Alert flow for drowsiness:
        Stage 1 (voice_delay seconds)    : Voice warning
        Stage 2 (buzzer_delay seconds)   : Buzzer alarm starts
        Stage 3 (emergency_delay seconds): SMS + GPS location + screenshot

    Alert flow for phone / distraction:
        Immediate voice warning on first detection
        SMS + GPS location after sustained detection
    """

    def __init__(
        self,
        alarm_path: str = "sounds/alarm.wav",
        screenshot_dir: str = "screenshots",
        voice_delay: float = 3.0,
        buzzer_delay: float = 8.0,
        emergency_delay: float = 13.0,
        twilio_sid: str = "",
        twilio_token: str = "",
        twilio_from: str = "",
        emergency_contact: str = "",
    ):
        self.screenshot_dir = Path(screenshot_dir)
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.voice_delay = voice_delay
        self.buzzer_delay = buzzer_delay
        self.emergency_delay = emergency_delay

        self._emergency_contact = emergency_contact
        self._twilio_client = None
        self._twilio_from = twilio_from

        # Twilio SMS client
        try:
            from twilio.rest import Client
            if twilio_sid and twilio_token:
                self._twilio_client = Client(twilio_sid, twilio_token)
                logger.info("Twilio SMS client initialized → alerts → %s", emergency_contact)
            else:
                logger.info("Twilio not configured. SMS alerts disabled.")
        except Exception as e:
            logger.warning("Twilio init failed: %s. SMS alerts disabled.", e)

        # Pygame alarm
        self._alarm = None
        self._alarm_playing = False
        try:
            import pygame
            pygame.mixer.init()
            if os.path.exists(alarm_path):
                self._alarm = pygame.mixer.Sound(alarm_path)
                logger.info("Alarm sound loaded from %s", alarm_path)
            else:
                logger.warning("Alarm file not found: %s", alarm_path)
        except Exception as e:
            logger.warning("Pygame init failed: %s. Buzzer alerts disabled.", e)

        # ── Alert state ─────────────────────────────────────────────
        # Drowsiness
        self._drowsy_start: Optional[float] = None
        self._drowsy_voice_sent: bool = False
        self._drowsy_buzzer_started: bool = False
        self._drowsy_emergency_sent: bool = False

        # Phone usage
        self._phone_start: Optional[float] = None
        self._phone_voice_sent: bool = False
        self._phone_sms_sent: bool = False

        # Distraction
        self._distraction_voice_sent: bool = False
        self._distraction_sms_sent: bool = False

    # ── Core Utilities ───────────────────────────────────────────────

    def speak(self, text: str) -> None:
        """Speak text using pyttsx3 in a background thread."""
        def _run():
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.setProperty("rate", 150)
                engine.setProperty("volume", 1.0)
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                logger.error("Voice alert failed: %s", e)
        threading.Thread(target=_run, daemon=True).start()

    def start_alarm(self) -> None:
        """Start the buzzer alarm (looping)."""
        if self._alarm and not self._alarm_playing:
            self._alarm.play(-1)
            self._alarm_playing = True
            logger.info("Buzzer alarm started")

    def stop_alarm(self) -> None:
        """Stop the buzzer alarm."""
        if self._alarm and self._alarm_playing:
            self._alarm.stop()
            self._alarm_playing = False
            logger.info("Buzzer alarm stopped")

    def capture_screenshot(self, frame: np.ndarray, reason: str) -> str:
        """Capture and save a screenshot.

        Args:
            frame: BGR image to save.
            reason: Event label used in filename.

        Returns:
            Absolute path to the saved screenshot.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.screenshot_dir / f"{reason}_{timestamp}.jpg"
        cv2.imwrite(str(filename), frame)
        logger.info("Screenshot saved: %s", filename)
        return str(filename)

    def get_gps_location(self) -> str:
        """Return accurate location string via multi-source IP geolocation.

        Tries multiple providers in order of accuracy:
          1. ip-api.com  — returns city, region, country + coordinates
          2. ipinfo.io   — returns city, region + coordinates
          3. geocoder    — fallback

        Returns:
            Formatted string with full address, coordinates, and Google Maps link.
        """
        import requests

        # ── Source 1: ip-api.com (most detailed, free) ──────────────
        try:
            resp = requests.get(
                "http://ip-api.com/json/?fields=status,city,regionName,country,lat,lon",
                timeout=5,
            )
            data = resp.json()
            if data.get("status") == "success":
                lat  = data["lat"]
                lng  = data["lon"]
                city = data.get("city", "")
                region = data.get("regionName", "")
                country = data.get("country", "")
                address = ", ".join(filter(None, [city, region, country]))
                maps_url = f"https://maps.google.com/?q={lat},{lng}"
                logger.info("GPS resolved via ip-api: %s (%.4f, %.4f)", address, lat, lng)
                return (
                    f"{address}\n"
                    f"Coordinates: {lat:.4f}, {lng:.4f}\n"
                    f"Maps: {maps_url}"
                )
        except Exception as e:
            logger.warning("ip-api GPS failed: %s", e)

        # ── Source 2: ipinfo.io (reliable fallback) ─────────────────
        try:
            resp = requests.get("https://ipinfo.io/json", timeout=5)
            data = resp.json()
            if "loc" in data:
                lat, lng = map(float, data["loc"].split(","))
                city    = data.get("city", "")
                region  = data.get("region", "")
                country = data.get("country", "")
                address = ", ".join(filter(None, [city, region, country]))
                maps_url = f"https://maps.google.com/?q={lat},{lng}"
                logger.info("GPS resolved via ipinfo: %s (%.4f, %.4f)", address, lat, lng)
                return (
                    f"{address}\n"
                    f"Coordinates: {lat:.4f}, {lng:.4f}\n"
                    f"Maps: {maps_url}"
                )
        except Exception as e:
            logger.warning("ipinfo GPS failed: %s", e)

        # ── Source 3: geocoder (last resort) ────────────────────────
        try:
            import geocoder
            g = geocoder.ip("me")
            if g.latlng:
                lat, lng = g.latlng
                maps_url = f"https://maps.google.com/?q={lat},{lng}"
                logger.info("GPS resolved via geocoder: %.4f, %.4f", lat, lng)
                return f"Coordinates: {lat:.4f}, {lng:.4f}\nMaps: {maps_url}"
        except Exception as e:
            logger.error("geocoder GPS failed: %s", e)

        return "Location unavailable"

    def send_sms(self, message: str) -> bool:
        """Send an SMS alert via Twilio.

        Args:
            message: SMS body text.

        Returns:
            True if the SMS was dispatched successfully.
        """
        if not self._twilio_client:
            logger.warning("SMS SKIPPED — Twilio not configured.")
            return False
        if not self._emergency_contact:
            logger.warning("SMS SKIPPED — No emergency contact number set.")
            return False
        try:
            msg = self._twilio_client.messages.create(
                body=message,
                from_=self._twilio_from,
                to=self._emergency_contact,
            )
            logger.info(
                "✅ SMS SENT to %s | SID: %s | Status: %s",
                self._emergency_contact, msg.sid, msg.status,
            )
            return True
        except Exception as e:
            logger.error("❌ SMS FAILED to %s | %s", self._emergency_contact, e)
            return False

    # ── Drowsiness Alert Pipeline ────────────────────────────────────

    def handle_drowsy(self, frame: np.ndarray, log_callback=None) -> str:
        """Handle drowsiness alert with staged escalation.

        Args:
            frame: Current video frame (used for screenshots).
            log_callback: Optional callable(event_str) for CSV logging.

        Returns:
            Current stage: 'monitoring', 'voice', 'buzzer', or 'emergency'.
        """
        if self._drowsy_start is None:
            self._drowsy_start = time.time()
            self._drowsy_voice_sent = False
            self._drowsy_buzzer_started = False
            self._drowsy_emergency_sent = False

        elapsed = time.time() - self._drowsy_start
        stage = "monitoring"

        # Stage 1 — voice warning
        if elapsed >= self.voice_delay and not self._drowsy_voice_sent:
            self.speak("Warning. Driver appears drowsy. Please stay alert.")
            self._drowsy_voice_sent = True
            if log_callback:
                log_callback("DROWSY_VOICE_WARNING")
            stage = "voice"

        # Stage 2 — buzzer alarm
        if elapsed >= self.buzzer_delay and not self._drowsy_buzzer_started:
            self.start_alarm()
            self._drowsy_buzzer_started = True
            if log_callback:
                log_callback("DROWSY_BUZZER_ALERT")
            stage = "buzzer"

        # Stage 3 — emergency SMS + screenshot
        # Buzzer intentionally kept ON — it stops only when the driver
        # opens their eyes and reset_drowsy() is called by the main loop.
        if elapsed >= self.emergency_delay and not self._drowsy_emergency_sent:
            location = self.get_gps_location()
            timestamp = datetime.now().strftime("%d-%b-%Y %I:%M %p")
            self.send_sms(
                f"🚨 NEXUS-DMS — EMERGENCY ALERT\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚠ Driver unresponsive for {elapsed:.0f}s!\n"
                f"🕐 Time: {timestamp}\n"
                f"📍 Location: {location}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Please check on the driver immediately."
            )
            self.speak("Critical alert. Driver is unresponsive. Emergency contact notified.")
            self.capture_screenshot(frame, "drowsy_emergency")
            self._drowsy_emergency_sent = True
            if log_callback:
                log_callback("DROWSY_EMERGENCY")
            stage = "emergency"

        return stage

    def reset_drowsy(self) -> None:
        """Reset drowsiness state when driver becomes alert again."""
        self._drowsy_start = None
        self._drowsy_voice_sent = False
        self._drowsy_buzzer_started = False
        self._drowsy_emergency_sent = False
        self.stop_alarm()

    @property
    def drowsy_elapsed(self) -> float:
        """Seconds elapsed since drowsiness was first detected."""
        if self._drowsy_start is None:
            return 0.0
        return time.time() - self._drowsy_start

    # ── Phone Detection Alert Pipeline ───────────────────────────────

    def handle_phone(
        self, frame: np.ndarray, phone_sms_delay: float = 5.0, log_callback=None
    ) -> None:
        """Handle mobile phone usage alerts.

        Speaks immediately on first detection; sends SMS + GPS after delay.
        """
        if not self._phone_voice_sent:
            self.speak("Warning. Mobile phone detected. Please focus on the road.")
            self._phone_voice_sent = True
            if log_callback:
                log_callback("PHONE_VOICE_WARNING")

        if self._phone_start is None:
            self._phone_start = time.time()

        elapsed = time.time() - self._phone_start
        if elapsed >= phone_sms_delay and not self._phone_sms_sent:
            self.capture_screenshot(frame, "phone_detected")
            location = self.get_gps_location()
            timestamp = datetime.now().strftime("%d-%b-%Y %I:%M %p")
            self.send_sms(
                f"📱 SAFE DRIVE AI — PHONE ALERT\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚠ Driver using mobile phone while driving!\n"
                f"🕐 Time: {timestamp}\n"
                f"📍 Location: {location}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Please put the phone down and focus on the road."
            )
            self._phone_sms_sent = True
            if log_callback:
                log_callback("PHONE_SMS_ALERT")

    def reset_phone(self) -> None:
        """Reset phone alert state."""
        self._phone_start = None
        self._phone_voice_sent = False
        self._phone_sms_sent = False

    # ── Distraction Alert ────────────────────────────────────────────

    def handle_distraction(
        self, frame: np.ndarray, direction: str, log_callback=None
    ) -> None:
        """Handle driver distraction — voice warning + SMS with GPS."""
        if not self._distraction_voice_sent:
            self.speak("Driver distraction detected. Please keep your eyes on the road.")
            self.capture_screenshot(frame, "distraction")
            self._distraction_voice_sent = True
            if log_callback:
                log_callback(f"DISTRACTION_{direction}")

        if not self._distraction_sms_sent:
            location = self.get_gps_location()
            timestamp = datetime.now().strftime("%d-%b-%Y %I:%M %p")
            self.send_sms(
                f"👀 SAFE DRIVE AI — DISTRACTION ALERT\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚠ Driver looking {direction} — not watching road!\n"
                f"🕐 Time: {timestamp}\n"
                f"📍 Location: {location}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Please keep your eyes on the road."
            )
            self._distraction_sms_sent = True

    def reset_distraction(self) -> None:
        """Reset distraction alert state."""
        self._distraction_voice_sent = False
        self._distraction_sms_sent = False

    # ── Cleanup ──────────────────────────────────────────────────────

    def cleanup(self) -> None:
        """Release all alert resources gracefully."""
        self.stop_alarm()
        try:
            import pygame
            pygame.mixer.quit()
        except Exception:
            pass
        logger.info("AlertManager cleaned up")
