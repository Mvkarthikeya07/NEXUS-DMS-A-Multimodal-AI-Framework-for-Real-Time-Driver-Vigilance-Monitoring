import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Centralized configuration for NEXUS-DMS."""
    
    # Paths
    BASE_DIR = Path(__file__).parent
    LOG_DIR = BASE_DIR / "logs"
    SCREENSHOT_DIR = BASE_DIR / "screenshots"
    SOUND_DIR = BASE_DIR / "sounds"
    MODEL_PATH = BASE_DIR / "yolov8m.pt"
    LOG_FILE = LOG_DIR / "alerts.csv"
    ALARM_FILE = SOUND_DIR / "alarm.wav"
    
    # Detection Thresholds
    EAR_THRESHOLD = float(os.getenv("EAR_THRESHOLD", "0.25"))
    MAR_THRESHOLD = float(os.getenv("MAR_THRESHOLD", "0.65"))
    DROWSY_FRAMES = int(os.getenv("DROWSY_FRAMES", "15"))
    HEAD_TURN_THRESHOLD = float(os.getenv("HEAD_TURN_THRESHOLD", "0.03"))
    PHONE_CONFIDENCE = float(os.getenv("PHONE_CONFIDENCE", "0.30"))
    
    # Alert Timing (seconds)
    VOICE_ALERT_DELAY      = float(os.getenv("VOICE_ALERT_DELAY",      "2.0"))
    BUZZER_ALERT_DELAY     = float(os.getenv("BUZZER_ALERT_DELAY",     "3.5"))
    EMERGENCY_ALERT_DELAY  = float(os.getenv("EMERGENCY_ALERT_DELAY",  "5.0"))
    DISTRACTION_ALERT_DELAY= float(os.getenv("DISTRACTION_ALERT_DELAY","3.0"))
    PHONE_SMS_DELAY        = float(os.getenv("PHONE_SMS_DELAY",        "5.0"))
    
    # Twilio SMS
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")
    EMERGENCY_CONTACT  = os.getenv("EMERGENCY_CONTACT", "")
    
    # Camera
    CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
    CAMERA_WIDTH = int(os.getenv("CAMERA_WIDTH", "640"))
    CAMERA_HEIGHT = int(os.getenv("CAMERA_HEIGHT", "480"))
    
    # MediaPipe
    MAX_NUM_FACES = 1
    MIN_DETECTION_CONFIDENCE = 0.5
    MIN_TRACKING_CONFIDENCE = 0.5
    REFINE_LANDMARKS = True
    
    # Landmark indices
    LEFT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
    RIGHT_EYE_INDICES = [362, 385, 387, 263, 373, 380]
    MOUTH_INDICES = [78, 81, 13, 311, 308, 402, 14, 178]
    NOSE_TIP_INDEX = 1
    LEFT_FACE_INDEX = 234
    RIGHT_FACE_INDEX = 454
    FOREHEAD_INDEX = 10
    CHIN_INDEX = 152
    
    # Flask Dashboard
    FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1")
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    
    @classmethod
    def ensure_directories(cls):
        """Create required directories if they don't exist."""
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
        cls.SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def is_twilio_configured(cls) -> bool:
        """Check if Twilio SMS credentials are properly configured."""
        return bool(
            cls.TWILIO_ACCOUNT_SID
            and cls.TWILIO_AUTH_TOKEN
            and cls.TWILIO_FROM_NUMBER
        )
