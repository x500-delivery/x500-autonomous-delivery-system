"""Package-label record: encode, decode and validate.

Field definitions follow docs/package-workflow.md. The numeric limits below are
placeholders until the team agrees tested values; they are not aircraft limits.
Standard library only.
"""
import json

SCHEMA_VERSION = 1
FIELDS = ("schema_version", "package_id", "mass_kg", "dimensions_mm", "destination_id")

# Placeholder limits. Replace with agreed, tested values.
MAX_MASS_KG = 1.5
MAX_DIMENSIONS_MM = (300, 300, 200)
MASS_TOLERANCE_KG = 0.05
MAX_ID_LENGTH = 32


class LabelError(ValueError):
    """The scanned text is not a readable label record."""


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def encode(record):
    """Return the compact text stored in the QR code."""
    return json.dumps({name: record[name] for name in FIELDS}, separators=(",", ":"))


def decode(text):
    """Parse scanned text into a record. Raises LabelError if it is not a label."""
    try:
        record = json.loads(text)
    except (TypeError, json.JSONDecodeError) as error:
        raise LabelError("label is not valid JSON") from error
    if not isinstance(record, dict):
        raise LabelError("label is not a JSON object")
    return record


def validate(record, approved_destinations=None, measured_mass_kg=None):
    """Return a list of rejection reasons; an empty list means the record is accepted.

    approved_destinations: collection of known destination IDs, or None to skip that check.
    measured_mass_kg: scale reading to cross-check against the label, or None to skip.
    """
    reasons = [f"missing field: {name}" for name in FIELDS if name not in record]
    if reasons:
        return reasons

    if record["schema_version"] != SCHEMA_VERSION:
        return [f"unsupported schema_version: {record['schema_version']!r}"]

    package_id = record["package_id"]
    if not isinstance(package_id, str) or not package_id.strip() or len(package_id) > MAX_ID_LENGTH:
        reasons.append(f"package_id must be a non-empty string of at most {MAX_ID_LENGTH} characters")

    mass = record["mass_kg"]
    mass_ok = _is_number(mass) and mass > 0
    if not mass_ok:
        reasons.append("mass_kg must be a positive number")
    elif mass > MAX_MASS_KG:
        reasons.append(f"mass_kg {mass} exceeds the limit of {MAX_MASS_KG} kg")

    dimensions = record["dimensions_mm"]
    if not (isinstance(dimensions, list) and len(dimensions) == 3
            and all(_is_number(side) and side > 0 for side in dimensions)):
        reasons.append("dimensions_mm must be three positive numbers")
    elif any(side > limit for side, limit in zip(sorted(dimensions, reverse=True), MAX_DIMENSIONS_MM)):
        reasons.append(f"dimensions_mm {dimensions} do not fit within {list(MAX_DIMENSIONS_MM)} mm")

    destination = record["destination_id"]
    if not isinstance(destination, str) or not destination:
        reasons.append("destination_id must be a non-empty string")
    elif approved_destinations is not None and destination not in approved_destinations:
        reasons.append(f"unknown destination_id: {destination}")

    if measured_mass_kg is not None and mass_ok and abs(mass - measured_mass_kg) > MASS_TOLERANCE_KG:
        reasons.append(
            f"label mass {mass} kg does not match measured mass {measured_mass_kg} kg "
            f"(tolerance {MASS_TOLERANCE_KG} kg)"
        )
    return reasons
