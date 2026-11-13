# Package label and delivery workflow

**Status: proposed integration specification.** Mohammed A and Ahmad jointly own the QR-code software: label generation, decoding, package-data format and validation. Ahmad also covers Jetson perception/runtime and is the proposed lead for autonomy integration.

## Start with one QR format

Use a versioned QR record generated from operator-entered package data. A destination ID resolves to a reviewed local site/route configuration. Keep private addresses out of public examples.

| Proposed field | Type / unit | Meaning |
| --- | --- | --- |
| `schema_version` | Integer | Format version; reject unsupported versions |
| `package_id` | String | Identity used across the label and mission record |
| `mass_kg` | Positive number | Gross package mass, including packaging and any package-side attachment plate |
| `dimensions_mm` | Three positive numbers | Length, width, height, in that order |
| `destination_id` | String | Approved delivery-site identifier |

Aircraft-side mount/retention mass belongs in the vehicle configuration. Agree size/length limits and numeric bounds before implementing the parser.

The label carries entered information; it does not measure the box or prove that its contents are correct. Cross-check mass using a scale and verify dimensions/fit. Automated dimension measurement can be a later perception feature. QR decoding/error correction is not proof that a label was created by an authorized sender.

## Separate the steps

1. **Generate and read:** Mohammed A and Ahmad develop generation, decoding and valid/invalid examples together; Ahmad also integrates the Jetson camera pipeline.
2. **Validate:** check version, units, required fields, numeric bounds and destination. Cross-check physical measurements and reject an incompatible package before planning.
3. **Evaluate routes:** enumerate approved candidate routes and estimate each one's full mission energy using Mohammed F and Jad's model. Select the feasible candidate with the lowest predicted energy; report ties, constraints and the fallback if none qualifies.
4. **Approve and execute:** show the operator the package, route, energy/reserve estimate and reasons. Only an approved mission proceeds to verified upload and execution.
5. **Record:** retain the package/mission IDs, input measurements, model/configuration versions, operator decision, state transitions and observed result.

This is constrained route selection for the first prototype. Arbitrary obstacle avoidance, multi-stop scheduling and learned control are separate extensions. A route's predicted feasibility does not establish that the delivery system is safe in all conditions.

## First demonstration

Run the complete decision flow on a laptop or Jetson with simulated aircraft I/O. Include a valid package plus malformed labels, unsupported versions, impossible dimensions/mass, unknown destinations, mass mismatch, insufficient battery, stale telemetry and duplicate active requests.

The demo should output either a proposed mission and its reasons or a clear rejection. No automatic arming or payload release is needed to demonstrate this software boundary.

A first laptop version is in [`software/package-labels/`](../software/package-labels/README.md) and [`software/companion/`](../software/companion/README.md). It covers label generation and reading, validation, mass mismatch, unknown destinations, wind limits and insufficient battery, using typed-in inputs, fictional sites and a placeholder energy estimate. Stale telemetry, duplicate requests, operator approval and aircraft I/O are not implemented yet.

[Architecture](architecture.md) · [Team responsibilities](team.md) · [Energy model](energy-model.md)
