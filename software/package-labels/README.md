# Package labels

**Owners: Mohammed A and Ahmad. Status: laptop demo; limits are placeholders.**

Defines the package record stored in a QR label, generates label images and validates scanned records. Fields follow the [package workflow](../../docs/package-workflow.md).

| File | Purpose |
| --- | --- |
| `label_schema.py` | Encode, decode and validate a record. Standard library only. |
| `generate_label.py` | Turn a record file into a QR PNG. |
| `examples/` | One valid record and deliberately invalid ones for testing. |

## Run

```bash
pip install -r software/package-labels/requirements.txt
python software/package-labels/generate_label.py software/package-labels/examples/valid.json
```

This writes `PKG-0001.png`. Read it back with the [companion demo](../companion/README.md).

## What validation checks

Required fields, schema version, package ID, positive mass and dimensions within limits, a known destination ID and, when a scale reading is supplied, agreement between labelled and measured mass.

`MAX_MASS_KG`, `MAX_DIMENSIONS_MM` and `MASS_TOLERANCE_KG` in `label_schema.py` are placeholders. Replace them with values agreed with the mechanical and energy-model owners. A label carries entered information; it does not prove what is in the box or who created it.
