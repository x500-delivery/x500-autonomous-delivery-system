"""Tests for the package-label record; all records here are test fixtures only."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "software" / "package-labels"))
import label_schema

SITES = {"SITE-A", "SITE-B"}


def record(**changes):
    result = {"schema_version": 1, "package_id": "PKG-0001", "mass_kg": 0.8,
              "dimensions_mm": [200, 150, 100], "destination_id": "SITE-A"}
    result.update(changes)
    return result


class LabelTests(unittest.TestCase):
    def test_valid_record_round_trips_and_is_accepted(self):
        decoded = label_schema.decode(label_schema.encode(record()))
        self.assertEqual(decoded, record())
        self.assertEqual(label_schema.validate(decoded, SITES, measured_mass_kg=0.82), [])

    def test_non_label_text_is_rejected(self):
        for text in ("not json", "[1, 2]", "", None):
            with self.assertRaises(label_schema.LabelError):
                label_schema.decode(text)

    def test_missing_field(self):
        broken = record()
        del broken["destination_id"]
        self.assertEqual(label_schema.validate(broken, SITES), ["missing field: destination_id"])

    def test_unsupported_version(self):
        self.assertIn("unsupported schema_version", label_schema.validate(record(schema_version=2), SITES)[0])

    def test_bad_mass(self):
        for mass in (0, -1, "0.8", True, None):
            self.assertIn("mass_kg must be a positive number", label_schema.validate(record(mass_kg=mass), SITES))
        self.assertIn("exceeds the limit", label_schema.validate(record(mass_kg=4.0), SITES)[0])

    def test_bad_dimensions(self):
        for dimensions in ([200, 150], [200, 150, 0], "200x150x100", [200, 150, "100"]):
            self.assertIn("dimensions_mm must be three positive numbers",
                          label_schema.validate(record(dimensions_mm=dimensions), SITES))
        self.assertIn("do not fit", label_schema.validate(record(dimensions_mm=[900, 150, 100]), SITES)[0])

    def test_dimension_order_does_not_matter(self):
        self.assertEqual(label_schema.validate(record(dimensions_mm=[100, 300, 250]), SITES), [])

    def test_unknown_destination(self):
        self.assertEqual(label_schema.validate(record(destination_id="SITE-Z"), SITES),
                         ["unknown destination_id: SITE-Z"])

    def test_bad_package_id(self):
        for package_id in ("", "   ", 7, "X" * 33):
            self.assertTrue(label_schema.validate(record(package_id=package_id), SITES))

    def test_mass_mismatch_with_scale(self):
        reasons = label_schema.validate(record(), SITES, measured_mass_kg=1.2)
        self.assertEqual(len(reasons), 1)
        self.assertIn("does not match measured mass", reasons[0])

    def test_example_files_match_their_names(self):
        import json
        examples = ROOT / "software" / "package-labels" / "examples"
        for path in sorted(examples.glob("*.json")):
            reasons = label_schema.validate(json.loads(path.read_text(encoding="utf-8")), SITES)
            self.assertEqual(reasons == [], path.name.startswith("valid"), path.name)


if __name__ == "__main__":
    unittest.main()
