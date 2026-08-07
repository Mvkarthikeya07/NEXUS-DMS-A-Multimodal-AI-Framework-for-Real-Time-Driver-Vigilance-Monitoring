"""Test alarm sound — Utility script for SafeDrive AI."""
import os
import sys
import time

import pygame


def main():
    pygame.mixer.init()

    alarm_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "sounds", "alarm.wav"
    )

    if not os.path.exists(alarm_path):
        print(f"ERROR: Alarm file not found: {alarm_path}")
        return

    alarm = pygame.mixer.Sound(alarm_path)
    print(f"Playing alarm from: {alarm_path}")
    alarm.play()
    time.sleep(5)
    alarm.stop()
    pygame.mixer.quit()
    print("Alarm test complete.")


if __name__ == "__main__":
    main()
