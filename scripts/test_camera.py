"""Test camera capture — Utility script for SafeDrive AI."""
import cv2
import sys


def main():
    backend = cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY
    cap = cv2.VideoCapture(0, backend)
    print("Camera opened:", cap.isOpened())

    if not cap.isOpened():
        print("ERROR: Cannot open camera.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame")
            break

        cv2.imshow("SafeDrive AI — Camera Test", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Camera test complete.")


if __name__ == "__main__":
    main()
