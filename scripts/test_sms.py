"""Test Twilio SMS — Utility script for SafeDrive AI.

Requires TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER,
and EMERGENCY_CONTACT environment variables to be set (or in .env file).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()


def main():
    sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    token = os.getenv("TWILIO_AUTH_TOKEN", "")
    from_number = os.getenv("TWILIO_FROM_NUMBER", "")
    to_number = os.getenv("EMERGENCY_CONTACT", "")

    if not all([sid, token, from_number, to_number]):
        print("ERROR: Twilio credentials not configured.")
        print("Set the following environment variables (or create a .env file):")
        print("  TWILIO_ACCOUNT_SID")
        print("  TWILIO_AUTH_TOKEN")
        print("  TWILIO_FROM_NUMBER")
        print("  EMERGENCY_CONTACT")
        return

    try:
        from twilio.rest import Client

        client = Client(sid, token)
        message = client.messages.create(
            body="SafeDrive AI — Test SMS sent successfully.",
            from_=from_number,
            to=to_number,
        )
        print(f"SMS sent! SID: {message.sid}")
    except Exception as e:
        print(f"SMS failed: {e}")


if __name__ == "__main__":
    main()
