"""Tests for route choice; sites, routes and energy numbers are invented fixtures."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "software" / "companion"))
sys.path.insert(0, str(ROOT / "software" / "package-labels"))
import demo
import energy_placeholder
import route_picker

SITES = route_picker.load_sites()
RECORD = {"schema_version": 1, "package_id": "PKG-0001", "mass_kg": 0.8,
          "dimensions_mm": [200, 150, 100], "destination_id": "SITE-A"}
ROUTE = SITES["SITE-A"]["routes"][0]


class EnergyTests(unittest.TestCase):
    def test_heavier_package_needs_more_energy(self):
        light = energy_placeholder.estimate_mission(ROUTE, 0.2)
        heavy = energy_placeholder.estimate_mission(ROUTE, 1.2)
        self.assertGreater(heavy["required_wh"], light["required_wh"])

    def test_wind_along_the_route_costs_energy(self):
        calm = energy_placeholder.estimate_mission(ROUTE, 0.8)
        windy = energy_placeholder.estimate_mission(ROUTE, 0.8, wind_speed_mps=5, wind_from_deg=0)
        self.assertGreater(windy["nominal_wh"], calm["nominal_wh"])

    def test_headwind_slows_and_tailwind_speeds_the_leg(self):
        params = energy_placeholder.PLACEHOLDER_PARAMS
        self.assertAlmostEqual(energy_placeholder.ground_speed_mps(0, 3, 0, params), 5.0)
        self.assertAlmostEqual(energy_placeholder.ground_speed_mps(0, 3, 180, params), 11.0)

    def test_required_covers_loaded_return_allowance_and_reserve(self):
        energy = energy_placeholder.estimate_mission(ROUTE, 0.8)
        self.assertGreater(energy["return_loaded_wh"], energy["phases"]["return_unloaded_wh"])
        self.assertGreater(energy["required_wh"], energy["nominal_wh"] + energy["reserve_wh"])

    def test_wind_at_airspeed_is_not_flyable(self):
        with self.assertRaises(energy_placeholder.RouteNotFlyable):
            energy_placeholder.estimate_mission(ROUTE, 0.8, wind_speed_mps=8, wind_from_deg=0)


class RoutePickerTests(unittest.TestCase):
    def test_calm_day_picks_lowest_energy_route(self):
        decision = route_picker.pick_route(RECORD, SITES, 100)
        self.assertTrue(decision["accepted"])
        self.assertEqual(decision["route_id"], "A-open-field")
        self.assertEqual(len(decision["considered"]), 2)

    def test_strong_wind_changes_the_chosen_route(self):
        decision = route_picker.pick_route(RECORD, SITES, 100, wind_speed_mps=7, wind_from_deg=90)
        self.assertTrue(decision["accepted"])
        self.assertEqual(decision["route_id"], "A-sheltered")
        self.assertTrue(any("A-open-field not used" in reason for reason in decision["reasons"]))

    def test_wind_above_every_limit_rejects(self):
        decision = route_picker.pick_route(RECORD, SITES, 100, wind_speed_mps=10)
        self.assertFalse(decision["accepted"])
        self.assertEqual(len(decision["reasons"]), 2)

    def test_low_battery_rejects(self):
        decision = route_picker.pick_route(RECORD, SITES, 15)
        self.assertFalse(decision["accepted"])
        self.assertTrue(all("Wh usable" in reason for reason in decision["reasons"]))

    def test_margin_is_battery_minus_required(self):
        decision = route_picker.pick_route(RECORD, SITES, 60)
        self.assertAlmostEqual(decision["margin_wh"], 60 - decision["energy"]["required_wh"])

    def test_unknown_destination_rejects(self):
        decision = route_picker.pick_route(dict(RECORD, destination_id="SITE-Z"), SITES, 100)
        self.assertFalse(decision["accepted"])


class DemoFlowTests(unittest.TestCase):
    def test_valid_label_text_gives_a_proposal(self):
        import label_schema
        record, decision = demo.decide(label_schema.encode(RECORD), SITES, 0.8, 60, 3, 0)
        self.assertEqual(record["package_id"], "PKG-0001")
        self.assertTrue(decision["accepted"])
        self.assertIn("PROPOSED ROUTE", demo.report(record, decision))

    def test_invalid_label_never_reaches_the_route_picker(self):
        for text in ("garbage", '{"schema_version": 1}'):
            record, decision = demo.decide(text, SITES, None, 60, 0, 0)
            self.assertFalse(decision["accepted"])
            self.assertEqual(decision["considered"], [])
            self.assertIn("REJECTED", demo.report(record, decision))

    def test_mass_mismatch_rejects_before_routing(self):
        import label_schema
        _, decision = demo.decide(label_schema.encode(RECORD), SITES, 1.2, 60, 0, 0)
        self.assertFalse(decision["accepted"])
        self.assertEqual(decision["considered"], [])


if __name__ == "__main__":
    unittest.main()
