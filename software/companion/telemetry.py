"""Battery and wind snapshot from Pixhawk MAVLink messages.

Turns SYS_STATUS, BATTERY_STATUS and WIND message fields into one snapshot, then
checks it is complete, fresh and above a minimum voltage. Standard library only;
read_pixhawk.py does the actual MAVLink connection.

The usable-energy rule and the limits below are placeholders, not measured X500
values. Mohammed F and Jad's energy work replaces usable_battery_wh().
"""
from dataclasses import dataclass

PACK_WH = 76.96            # Tattu 4S 5200 mAh nominal rating (hardware/README.md)
USABLE_FRACTION = 0.8      # placeholder share of the pack treated as usable
MAX_AGE_S = 3.0
MIN_VOLTAGE_V = 14.8       # placeholder: 3.7 V per cell for a 4S pack at rest

# MAVLink "unknown" markers for these fields.
_UNKNOWN_VOLTAGE_MV = 0xFFFF
_UNKNOWN_CURRENT_CA = -1
_UNKNOWN_REMAINING = -1
_UNKNOWN_ENERGY_HJ = -1


@dataclass
class Telemetry:
    voltage_v: float = None
    current_a: float = None
    remaining_pct: float = None
    energy_used_wh: float = None
    wind_speed_mps: float = None
    wind_from_deg: float = None
    battery_time: float = None
    wind_time: float = None


def _fields(message):
    if message is None:
        return None
    return message.to_dict() if hasattr(message, "to_dict") else message


def from_messages(sys_status=None, battery_status=None, wind=None, battery_time=None, wind_time=None):
    """Build a Telemetry from message fields (pymavlink messages or plain dicts).

    battery_time and wind_time are when the messages arrived, in time.monotonic() seconds.
    """
    t = Telemetry(battery_time=battery_time, wind_time=wind_time)
    status = _fields(sys_status)
    if status:
        if status.get("voltage_battery") not in (None, _UNKNOWN_VOLTAGE_MV):
            t.voltage_v = status["voltage_battery"] / 1000
        if status.get("current_battery") not in (None, _UNKNOWN_CURRENT_CA):
            t.current_a = status["current_battery"] / 100
        if status.get("battery_remaining") not in (None, _UNKNOWN_REMAINING):
            t.remaining_pct = float(status["battery_remaining"])
    battery = _fields(battery_status)
    if battery:
        if battery.get("energy_consumed") not in (None, _UNKNOWN_ENERGY_HJ):
            t.energy_used_wh = battery["energy_consumed"] * 100 / 3600
        if t.remaining_pct is None and battery.get("battery_remaining") not in (None, _UNKNOWN_REMAINING):
            t.remaining_pct = float(battery["battery_remaining"])
    air = _fields(wind)
    if air:
        t.wind_speed_mps = float(air["speed"])
        t.wind_from_deg = float(air["direction"]) % 360
    return t


def usable_battery_wh(t, pack_wh=PACK_WH, usable_fraction=USABLE_FRACTION):
    """PLACEHOLDER: usable energy left = pack rating x usable share x remaining %."""
    if t.remaining_pct is None:
        return None
    return pack_wh * usable_fraction * t.remaining_pct / 100


def check(t, now, max_age_s=MAX_AGE_S, min_voltage_v=MIN_VOLTAGE_V):
    """Return a list of problems with the snapshot; an empty list means it can be used."""
    problems = []
    if t.voltage_v is None or t.battery_time is None:
        problems.append("no battery voltage received")
    elif t.voltage_v < min_voltage_v:
        problems.append(f"battery voltage {t.voltage_v:.2f} V is below the minimum of {min_voltage_v:.2f} V")
    if t.remaining_pct is None:
        problems.append("battery remaining % is unknown; check the battery monitor setup")
    if t.wind_speed_mps is None or t.wind_time is None:
        problems.append("no wind estimate received")
    for name, received in (("battery", t.battery_time), ("wind", t.wind_time)):
        if received is not None and now - received > max_age_s:
            problems.append(f"{name} data is {now - received:.1f} s old (limit {max_age_s:.1f} s)")
    return problems


def demo_arguments(t):
    """Return the demo.py arguments for this snapshot, or None if it is incomplete."""
    usable = usable_battery_wh(t)
    if usable is None or t.wind_speed_mps is None:
        return None
    return f"--battery-wh {usable:.1f} --wind-speed {t.wind_speed_mps:.1f} --wind-from {t.wind_from_deg:.0f}"


def summary(t, now):
    """Human-readable snapshot."""
    def show(value, fmt, unit):
        return "unknown" if value is None else f"{value:{fmt}}{unit}"

    usable = usable_battery_wh(t)
    lines = [
        f"Battery: {show(t.voltage_v, '.2f', ' V')}, {show(t.current_a, '.1f', ' A')}, "
        f"{show(t.remaining_pct, '.0f', ' %')} remaining, {show(t.energy_used_wh, '.1f', ' Wh')} used",
        f"  usable estimate: {show(usable, '.1f', ' Wh')} (placeholder rule)",
        f"Wind: {show(t.wind_speed_mps, '.1f', ' m/s')} from {show(t.wind_from_deg, '.0f', ' deg')} "
        "(ArduPilot estimate; only meaningful in flight)",
        "Data age: " + ", ".join(
            f"{name} {show(None if received is None else now - received, '.1f', ' s')}"
            for name, received in (("battery", t.battery_time), ("wind", t.wind_time))),
    ]
    return "\n".join(lines)
