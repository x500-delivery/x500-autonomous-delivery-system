"""Read the text of a QR label from an image file or a camera.

Usage:
    python software/companion/scan_label.py --image PKG-0001.png
    python software/companion/scan_label.py --camera 0

Requires OpenCV (see requirements.txt). On the Jetson, use the OpenCV build that
ships with JetPack; a CSI camera needs a GStreamer pipeline instead of an index.
"""
import argparse
import time


def _cv2():
    try:
        import cv2
    except ImportError as error:
        raise SystemExit("Install the companion requirements first: "
                         "pip install -r software/companion/requirements.txt") from error
    return cv2


def scan_image(path):
    """Return the QR text found in an image file, or None."""
    cv2 = _cv2()
    frame = cv2.imread(str(path))
    if frame is None:
        raise SystemExit(f"Could not read image: {path}")
    text, _, _ = cv2.QRCodeDetector().detectAndDecode(frame)
    return text or None


def scan_camera(index=0, timeout_s=30.0):
    """Return the first QR text seen by the camera within the timeout, or None."""
    cv2 = _cv2()
    capture = cv2.VideoCapture(index)
    if not capture.isOpened():
        raise SystemExit(f"Could not open camera {index}")
    detector = cv2.QRCodeDetector()
    deadline = time.monotonic() + timeout_s
    try:
        while time.monotonic() < deadline:
            ok, frame = capture.read()
            if not ok:
                continue
            text, _, _ = detector.detectAndDecode(frame)
            if text:
                return text
    finally:
        capture.release()
    return None


def main():
    parser = argparse.ArgumentParser(description="Read a QR label.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--image", help="image file containing the label")
    source.add_argument("--camera", type=int, help="camera index, usually 0")
    parser.add_argument("--timeout", type=float, default=30.0, help="seconds to wait for a camera read")
    args = parser.parse_args()

    text = scan_image(args.image) if args.image else scan_camera(args.camera, args.timeout)
    if not text:
        raise SystemExit("No QR label found")
    print(text)


if __name__ == "__main__":
    main()
