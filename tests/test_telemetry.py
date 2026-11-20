"""Tests for the Pixhawk snapshot; message values here are invented fixtures."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "software" / "companion"))
import telemetry

SYS_STATUS = {"voltage_battery": 15900, "current_battery": 120, "battery_remaining": 62}
BATTERY_STATUS = {"energy_consumed": 122, "battery_remaining": 62}
WIND = {"direction": -45.0, "speed": 2.8, "speed_z": 0.0}


def snapshot(**changes):
    values = {"sys_status": SYS_STATUS, "battery_status": BATTERY_STATUS, "wind": WIND,
              "battery_time": 100.0, "wind_time": 100.0}
    values.update(changes)
    return telemetry.from_messages(**values)


class ConversionTests(unittest.TestCase):
    def test_units_are_converted(self):
        t = snapshot()
        self.assertAlmostEqual(t.voltage_v, 15.9)
        self.assertAlmostEqual(t.current_a, 1.2)
        self.assertEqual(t.remaining_pct, 62)
        self.assertAlmostEqual(t.energy_used_wh, 122 * 100 / 3600)
        self.assertAlmostEqual(t.wind_speed_mps, 2.8)
        self.assertAlmostEqual(t.wind_from_deg, 315)

    def test_unknown_markers_become_none(self):
        t = snapshot(sys_status={"voltage_battery": 0xFFFF, "current_battery": -1, "battery_remaining": -1},
                     battery_status={"energy_consumed": -1, "battery_remaining": -1})
        self.assertIsNone(t.voltage_v)
        self.assertIsNone(t.current_a)
        self.assertIsNone(t.remaining_pct)
        self.assertIsNone(t.energy_used_wh)

    def test_remaining_falls_back_to_battery_status(self):
        t = snapshot(sys_status={"voltage_battery": 15900, "battery_remaining": -1},
                     battery_status={"battery_remaining": 40})
        self.assertEqual(t.remaining_pct, 40)

    def test_pymavlink_style_messages_are_accepted(self):
        class Message:
            def __init__(self, fields):
                self.fields = fields

            def to_dict(self):
                return self.fields

        t = telemetry.from_messages(Message(SYS_STATUS), Message(BATTERY_STATUS), Message(WIND), 1.0, 1.0)
        self.assertAlmostEqual(t.voltage_v, 15.9)


class CheckTests(unittest.TestCase):
    def test_good_snapshot_has_no_problems(self):
        self.assertEqual(telemetry.check(snapshot(), now=101.0), [])

    def test_usable_energy_placeholder_rule(self):
        self.assertAlmostEqual(telemetry.usable_battery_wh(snapshot()), 76.96 * 0.8 * 0.62)

    def test_low_voltage_is_flagged(self):
        t = snapshot(sys_status=dict(SYS_STATUS, voltage_battery=14500))
        self.assertIn("below the minimum", telemetry.check(t, now=101.0)[0])

    def test_missing_data_is_flagged(self):
        problems = telemetry.check(telemetry.from_messages(), now=101.0)
        self.assertIn("no battery voltage received", problems)
        self.assertIn("no wind estimate received", problems)
        self.assertTrue(any("remaining % is unknown" in p for p in problems))

    def test_stale_data_is_flagged(self):
        problems = telemetry.check(snapshot(wind_time=90.0), now=101.0)
        self.assertEqual(len(problems), 1)
        self.assertIn("wind data is 11.0 s old", problems[0])

    def test_demo_arguments(self):
        self.assertEqual(telemetry.demo_arguments(snapshot()),
                         "--battery-wh 38.2 --wind-speed 2.8 --wind-from 315")
        self.assertIsNone(telemetry.demo_arguments(snapshot(wind=None)))

    def test_summary_handles_missing_values(self):
        text = telemetry.summary(telemetry.from_messages(), now=1.0)
        self.assertIn("unknown", text)


if __name__ == "__main__":
    unittest.main()
