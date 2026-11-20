"""Read a battery and wind snapshot from the Pixhawk. Read-only.

Usage:
    python software/companion/read_pixhawk.py                          # Jetson, USB: /dev/ttyACM0
    python software/companion/read_pixhawk.py --connect COM5           # Windows laptop
    python software/companion/read_pixhawk.py --connect tcp:127.0.0.1:5762   # simulator

It never arms, changes mode or uploads a mission. The only messages it sends ask
the Pixhawk to stream SYS_STATUS, BATTERY_STATUS and WIND (skip with --no-request).
Requires pymavlink (see requirements.txt).
"""
import argparse
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import telemetry

STREAM_HZ = 2


def _mavutil():
    try:
        from pymavlink import mavutil
    except ImportError as error:
        raise SystemExit("Install the companion requirements first: "
                         "pip install -r software/companion/requirements.txt") from error
    return mavutil


def request_streams(link, mavutil):
    """Ask for the three messages at STREAM_HZ. Changes no flight behaviour."""
    for name in ("SYS_STATUS", "BATTERY_STATUS", "WIND"):
        message_id = getattr(mavutil.mavlink, f"MAVLINK_MSG_ID_{name}")
        link.mav.command_long_send(
            link.target_system, link.target_component,
            mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL, 0,
            message_id, 1_000_000 / STREAM_HZ, 0, 0, 0, 0, 0)


def read_snapshot(connect, baud=115200, timeout_s=10.0, request=True):
    """Return (Telemetry, now) from the latest messages received within the timeout."""
    mavutil = _mavutil()
    link = mavutil.mavlink_connection(connect, baud=baud, dialect="ardupilotmega")
    try:
        if link.wait_heartbeat(timeout=timeout_s) is None:
            raise SystemExit(f"No heartbeat from {connect} within {timeout_s:.0f} s. "
                             "Check the cable, the port name and that nothing else is using the port.")
        if request:
            request_streams(link, mavutil)

        latest, received = {}, {}
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline and len(latest) < 3:
            message = link.recv_match(type=["SYS_STATUS", "BATTERY_STATUS", "WIND"],
                                      blocking=True, timeout=0.5)
            if message is not None:
                latest[message.get_type()] = message
                received[message.get_type()] = time.monotonic()
    finally:
        link.close()

    battery_times = [received[n] for n in ("SYS_STATUS", "BATTERY_STATUS") if n in received]
    snapshot = telemetry.from_messages(
        latest.get("SYS_STATUS"), latest.get("BATTERY_STATUS"), latest.get("WIND"),
        battery_time=min(battery_times) if battery_times else None,
        wind_time=received.get("WIND"))
    return snapshot, time.monotonic()


def main():
    parser = argparse.ArgumentParser(description="Read battery and wind from the Pixhawk (read-only).")
    parser.add_argument("--connect", default="/dev/ttyACM0",
                        help="serial port or MAVLink address (default /dev/ttyACM0)")
    parser.add_argument("--baud", type=int, default=115200, help="serial baud rate")
    parser.add_argument("--timeout", type=float, default=10.0, help="seconds to wait for data")
    parser.add_argument("--no-request", action="store_true", help="do not ask for message streams")
    parser.add_argument("--json", action="store_true", help="print the snapshot as JSON")
    args = parser.parse_args()

    snapshot, now = read_snapshot(args.connect, args.baud, args.timeout, not args.no_request)
    problems = telemetry.check(snapshot, now)
    if args.json:
        print(json.dumps({"snapshot": vars(snapshot), "usable_wh": telemetry.usable_battery_wh(snapshot),
                          "problems": problems}, indent=2))
    else:
        print(telemetry.summary(snapshot, now))
        arguments = telemetry.demo_arguments(snapshot)
        if arguments:
            print(f"Demo arguments: {arguments}")
        if problems:
            print("NOT USABLE")
            print("\n".join(f"  - {problem}" for problem in problems))
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
