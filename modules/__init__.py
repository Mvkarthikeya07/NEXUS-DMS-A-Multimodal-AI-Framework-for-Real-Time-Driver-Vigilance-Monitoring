"""NEXUS-DMS detection modules.

Uses lazy imports to avoid triggering heavy dependency chains
(mediapipe → tensorflow → jax) at package import time.
Individual modules are imported directly where needed.
"""

__all__ = [
    "Camera",
    "FaceAnalyzer",
    "FaceData",
    "DrowsinessDetector",
    "YawnDetector",
    "DistractionDetector",
    "PhoneDetector",
    "AlertManager",
]


def __getattr__(name: str):
    """Lazy import for package-level access."""
    if name == "Camera":
        from modules.camera import Camera
        return Camera
    elif name == "FaceAnalyzer":
        from modules.face_analyzer import FaceAnalyzer
        return FaceAnalyzer
    elif name == "FaceData":
        from modules.face_analyzer import FaceData
        return FaceData
    elif name == "DrowsinessDetector":
        from modules.drowsiness import DrowsinessDetector
        return DrowsinessDetector
    elif name == "YawnDetector":
        from modules.yawn_detector import YawnDetector
        return YawnDetector
    elif name == "DistractionDetector":
        from modules.distraction_detector import DistractionDetector
        return DistractionDetector
    elif name == "PhoneDetector":
        from modules.phone_detector import PhoneDetector
        return PhoneDetector
    elif name == "AlertManager":
        from modules.alert_manager import AlertManager
        return AlertManager
    raise AttributeError(f"module 'modules' has no attribute {name!r}")
