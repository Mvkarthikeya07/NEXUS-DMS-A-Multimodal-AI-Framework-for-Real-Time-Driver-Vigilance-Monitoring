"""Test voice TTS — Utility script for SafeDrive AI."""
import pyttsx3


def main():
    engine = pyttsx3.init()
    engine.setProperty("rate", 150)
    engine.setProperty("volume", 1.0)
    engine.say("SafeDrive AI voice test successful.")
    engine.runAndWait()
    print("Voice test complete.")


if __name__ == "__main__":
    main()
