"""Generate a QR label image from a package record.

Usage:
    python software/package-labels/generate_label.py software/package-labels/examples/valid.json
    python software/package-labels/generate_label.py record.json --out label.png

Requires the `qrcode` package (see requirements.txt).
"""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import label_schema


def make_label(record, out_path):
    """Write the record as a QR PNG. Raises ValueError if the record is not well formed."""
    reasons = label_schema.validate(record)
    if reasons:
        raise ValueError("; ".join(reasons))
    try:
        import qrcode
    except ImportError as error:
        raise SystemExit("Install the label requirements first: "
                         "pip install -r software/package-labels/requirements.txt") from error
    image = qrcode.make(label_schema.encode(record), error_correction=qrcode.constants.ERROR_CORRECT_M)
    image.save(out_path)


def main():
    parser = argparse.ArgumentParser(description="Generate a QR label from a package record.")
    parser.add_argument("record", type=Path, help="JSON file containing the package record")
    parser.add_argument("--out", type=Path, help="output PNG (default: <package_id>.png)")
    args = parser.parse_args()

    record = json.loads(args.record.read_text(encoding="utf-8"))
    out_path = args.out or Path(f"{record.get('package_id', 'label')}.png")
    try:
        make_label(record, out_path)
    except ValueError as error:
        raise SystemExit(f"Record rejected: {error}")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
