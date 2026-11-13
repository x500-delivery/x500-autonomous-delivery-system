# Companion software

**Owners: Ahmad (camera and runtime) and Alend (mission integration), with Mohammed A. Status: laptop demo with typed-in inputs and a placeholder energy model. Nothing here arms, flies or releases anything.**

Reads a package label, validates it and proposes one of the approved routes to its destination, or rejects it with reasons.

| File | Purpose | Replace with |
| --- | --- | --- |
| `scan_label.py` | Read QR text from an image or camera (OpenCV) | Jetson camera pipeline once a camera is chosen |
| `sites.json` | Destinations and candidate routes. **Fictional.** | Surveyed, approved sites and routes, kept out of public examples if private |
| `energy_placeholder.py` | Mission watt-hours by phase. **Invented numbers.** | The fitted [energy model](../../docs/energy-model.md) |
| `route_picker.py` | Drop routes outside their wind limit or energy budget; propose the lowest-energy feasible route | Keep; feed it Pixhawk battery and wind data |
| `demo.py` | Runs the whole flow from the command line | Mission manager with operator approval and MAVLink upload |

## Run

```bash
pip install -r software/companion/requirements.txt
python software/companion/demo.py --record software/package-labels/examples/valid.json --measured-mass 0.8 --battery-wh 60 --wind-speed 3 --wind-from 0
```

Use `--image label.png` or `--camera 0` in place of `--record` to scan a real label. Try `--wind-speed 7 --wind-from 90 --battery-wh 100` to see the route change, and `--battery-wh 15` to see a rejection. `--wind-from` is the direction the wind blows from, in degrees.

The `--record` path and the tests need only Python 3.10+. OpenCV is needed only for `--image` and `--camera`.

## How a route is chosen

1. A route is dropped if the wind is above that route's tested limit.
2. The energy estimate covers climb, loaded outbound flight, placement hover and return. The required figure assumes returning with the package, then adds an uncertainty allowance and a reserve.
3. A route is dropped if the required energy exceeds the usable battery energy.
4. The remaining route with the lowest nominal energy is proposed, with reasons. The operator still decides.

In steady wind the shortest route normally needs the least energy, so wind mostly changes which routes are allowed and whether the battery is enough.

## Running on the Jetson

The Jetson has network access on the ground only. Everything it needs in flight must already be on its disk.

1. Once, on the ground with Wi-Fi: clone the repository, create a virtual environment and install the requirements. Use the OpenCV build that ships with JetPack if `pip` has no suitable one.
2. To update, on the ground with Wi-Fi: `git pull`, or check out a tagged version, then run the tests on the Jetson.
3. Run only reviewed code from `main` or a tag on the aircraft, and record the commit in the test record.

```bash
git clone https://github.com/x500-delivery/x500-autonomous-delivery-system.git
cd x500-autonomous-delivery-system
python3 -m venv .venv
source .venv/bin/activate
pip install -r software/package-labels/requirements.txt -r software/companion/requirements.txt
python -m unittest discover -s tests -v
```

Battery state and the wind estimate are to come from the Pixhawk over MAVLink; that connection is not implemented here.
