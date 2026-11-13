# Software

## Runnable now

[Flight-summary analysis](../analysis/summarize_segments.py) is an offline Python 3.10+ utility using only the standard library. It validates the included CSV and generates Markdown/JSON reports. See [run instructions](../README.md#run-the-analysis).

The [package-label tools](package-labels/README.md) and [companion demo](companion/README.md) run the label-to-route decision on a laptop: generate a QR label, read it, validate the record and propose an approved route or reject it. Battery, wind and measured mass are typed in, the sites are fictional and the energy numbers are placeholders. It does not communicate with the aircraft.

## Delivery software under development

| Component | Owner | Responsibility |
| --- | --- | --- |
| QR-code software and package intake | Mohammed A + Ahmad | Generate/read QR labels, define versioned package records and validate decoded data |
| Jetson perception and runtime | Ahmad | Camera acquisition, label decoding and reproducible onboard software environment |
| Jetson–Pixhawk communication and mission integration | Alend, with Mohammed A + Ahmad | Generate flight paths from validated package data, integrate route/energy evaluation, upload missions and monitor execution |
| Energy estimator | Mohammed F + Jad | Predict mission Wh and uncertainty from calibrated measurements |
| System integration | Mohammed F | Agree interfaces, aircraft constraints and end-to-end tests with subsystem owners |

Mohammed A and Ahmad provide the validated package-data pipeline; Ahmad maintains the Jetson camera/runtime environment. Alend connects that pipeline to mission planning and the Pixhawk interface, using the energy estimator developed by Mohammed F and Jad.

The label describes a delivery request. The validator, energy estimator, route evaluator and operator must all accept it before execution. See [package workflow](../docs/package-workflow.md) and [energy model](../docs/energy-model.md).

Label code lives in `software/package-labels/` and Jetson-side code in `software/companion/`; keep offline model work in `analysis/energy-model/`. Each component should include a small runnable example, dependency versions and tests for its inputs and failure cases.

Develop against simulated aircraft I/O first. Record the actual JetPack/Jetson Linux version and camera/MAVLink configuration when hardware integration begins. ML/RL experiments should have their own reproducible evaluations and a baseline comparison.
