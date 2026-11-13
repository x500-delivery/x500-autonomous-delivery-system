"""Choose among the approved routes to a destination.

For each approved route: check the wind is within the route's tested limit, estimate
the mission energy, and check it against the usable battery energy. The feasible
route with the lowest nominal energy is proposed. The result is a proposal for the
operator, not permission to fly. Standard library only.
"""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import energy_placeholder

DEFAULT_SITES = Path(__file__).resolve().parent / "sites.json"


def load_sites(path=DEFAULT_SITES):
    """Return {destination_id: site} from the approved-sites file."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data["sites"]


def pick_route(record, sites, battery_usable_wh, wind_speed_mps=0.0, wind_from_deg=0.0, params=None):
    """Return a decision dict: accepted, route_id, energy, margin_wh, reasons, considered."""
    site = sites.get(record["destination_id"])
    if site is None:
        return {"accepted": False, "reasons": [f"unknown destination_id: {record['destination_id']}"],
                "considered": []}

    considered = []
    for route in site["routes"]:
        entry = {"route_id": route["id"], "feasible": False, "reasons": []}
        considered.append(entry)
        if wind_speed_mps > route["max_wind_mps"]:
            entry["reasons"].append(
                f"wind {wind_speed_mps:.1f} m/s is above this route's limit of {route['max_wind_mps']:.1f} m/s")
            continue
        try:
            energy = energy_placeholder.estimate_mission(
                route, record["mass_kg"], wind_speed_mps, wind_from_deg, params)
        except energy_placeholder.RouteNotFlyable as error:
            entry["reasons"].append(str(error))
            continue
        entry["energy"] = energy
        entry["margin_wh"] = battery_usable_wh - energy["required_wh"]
        if entry["margin_wh"] < 0:
            entry["reasons"].append(
                f"needs {energy['required_wh']:.1f} Wh including allowance and reserve; "
                f"only {battery_usable_wh:.1f} Wh usable")
            continue
        entry["feasible"] = True

    feasible = [entry for entry in considered if entry["feasible"]]
    if not feasible:
        return {"accepted": False, "considered": considered,
                "reasons": [f"{entry['route_id']}: {reason}" for entry in considered for reason in entry["reasons"]]}

    best = min(feasible, key=lambda entry: entry["energy"]["nominal_wh"])
    reasons = [f"lowest predicted energy of {len(feasible)} feasible route(s): "
               f"{best['energy']['nominal_wh']:.1f} Wh nominal",
               f"{best['margin_wh']:.1f} Wh margin after allowance and reserve"]
    reasons += [f"{entry['route_id']} not used: {reason}"
                for entry in considered if not entry["feasible"] for reason in entry["reasons"]]
    return {"accepted": True, "route_id": best["route_id"], "energy": best["energy"],
            "margin_wh": best["margin_wh"], "reasons": reasons, "considered": considered}
