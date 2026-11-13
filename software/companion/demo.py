"""End-to-end laptop demo: read a label, validate it, propose a route or reject.

Usage:
    python software/companion/demo.py --record software/package-labels/examples/valid.json \
        --measured-mass 0.8 --battery-wh 60 --wind-speed 3 --wind-from 0
    python software/companion/demo.py --image PKG-0001.png --measured-mass 0.8 --battery-wh 60
    python software/companion/demo.py --camera 0 --measured-mass 0.8 --battery-wh 60

Battery, wind and measured mass are typed in here. On the aircraft they are to come
from the Pixhawk and a scale. The energy numbers are placeholders. Nothing in this
demo arms, flies or releases anything.
"""
import argparse
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "package-labels"))
import label_schema
import route_picker


def decide(text, sites, measured_mass_kg, battery_usable_wh, wind_speed_mps, wind_from_deg):
    """Run decode, validation and route choice on scanned label text."""
    try:
        record = label_schema.decode(text)
    except label_schema.LabelError as error:
        return None, {"accepted": False, "reasons": [str(error)], "considered": []}
    reasons = label_schema.validate(record, approved_destinations=sites, measured_mass_kg=measured_mass_kg)
    if reasons:
        return record, {"accepted": False, "reasons": reasons, "considered": []}
    return record, route_picker.pick_route(record, sites, battery_usable_wh, wind_speed_mps, wind_from_deg)


def report(record, decision):
    lines = []
    if record:
        lines.append(f"Package {record.get('package_id')}: {record.get('mass_kg')} kg, "
                     f"{record.get('dimensions_mm')} mm, to {record.get('destination_id')}")
    if decision["accepted"]:
        energy = decision["energy"]
        lines.append(f"PROPOSED ROUTE: {decision['route_id']}  (operator approval still required)")
        lines.append(f"  Energy model: {energy['model']}")
        for name, value in energy["phases"].items():
            lines.append(f"  {name:<22}{value:6.1f} Wh")
        lines.append(f"  {'required incl. reserve':<22}{energy['required_wh']:6.1f} Wh")
        lines.append(f"  {'flight time':<22}{energy['flight_time_s'] / 60:6.1f} min")
    else:
        lines.append("REJECTED")
    lines += [f"  - {reason}" for reason in decision["reasons"]]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Laptop demo of label intake and route choice.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--record", type=Path, help="JSON record file (skips the camera)")
    source.add_argument("--image", help="image file containing a QR label")
    source.add_argument("--camera", type=int, help="camera index, usually 0")
    parser.add_argument("--measured-mass", type=float, help="scale reading in kg, to cross-check the label")
    parser.add_argument("--battery-wh", type=float, required=True, help="usable battery energy remaining, Wh")
    parser.add_argument("--wind-speed", type=float, default=0.0, help="wind speed, m/s")
    parser.add_argument("--wind-from", type=float, default=0.0, help="direction the wind blows from, degrees")
    parser.add_argument("--sites", type=Path, default=route_picker.DEFAULT_SITES, help="approved sites file")
    args = parser.parse_args()

    if args.record:
        text = args.record.read_text(encoding="utf-8")
    else:
        import scan_label
        text = scan_label.scan_image(args.image) if args.image else scan_label.scan_camera(args.camera)
        if not text:
            raise SystemExit("No QR label found")

    record, decision = decide(text, route_picker.load_sites(args.sites), args.measured_mass,
                              args.battery_wh, args.wind_speed, args.wind_from)
    print(report(record, decision))
    sys.exit(0 if decision["accepted"] else 1)


if __name__ == "__main__":
    main()
