"""PLACEHOLDER mission-energy estimate for the laptop demo.

Every number in PLACEHOLDER_PARAMS is invented so the demo can run. None of it is
measured X500 data or a recommended limit. Mohammed F and Jad's fitted model
(docs/energy-model.md) replaces this module; keep the estimate_mission() interface.
Standard library only.
"""
import math

PLACEHOLDER_PARAMS = {
    "base_mass_kg": 2.2,          # aircraft without package
    "hover_power_w": 260.0,       # at base mass
    "airspeed_mps": 8.0,
    "climb_rate_mps": 2.0,
    "descent_rate_mps": 1.5,
    "climb_power_factor": 1.2,
    "placement_hover_s": 30.0,
    "uncertainty_fraction": 0.15,
    "reserve_wh": 10.0,
    "min_ground_speed_mps": 1.0,
}


class RouteNotFlyable(ValueError):
    """The wind leaves too little ground speed on a leg."""


def _power_w(total_mass_kg, params):
    # Hover power grows roughly with mass^1.5 (momentum theory).
    return params["hover_power_w"] * (total_mass_kg / params["base_mass_kg"]) ** 1.5


def ground_speed_mps(heading_deg, wind_speed_mps, wind_from_deg, params):
    """Speed along the leg for a fixed airspeed. wind_from_deg is where the wind blows from."""
    angle = math.radians(wind_from_deg - heading_deg)
    headwind = wind_speed_mps * math.cos(angle)
    crosswind = wind_speed_mps * math.sin(angle)
    airspeed = params["airspeed_mps"]
    if abs(crosswind) >= airspeed:
        raise RouteNotFlyable(f"crosswind {abs(crosswind):.1f} m/s is at or above airspeed")
    speed = math.sqrt(airspeed ** 2 - crosswind ** 2) - headwind
    if speed < params["min_ground_speed_mps"]:
        raise RouteNotFlyable(f"ground speed {speed:.1f} m/s on heading {heading_deg} is too low")
    return speed


def _legs_time_s(legs, reverse, wind_speed_mps, wind_from_deg, params):
    total = 0.0
    for leg in legs:
        heading = (leg["heading_deg"] + 180) % 360 if reverse else leg["heading_deg"]
        total += leg["distance_m"] / ground_speed_mps(heading, wind_speed_mps, wind_from_deg, params)
    return total


def estimate_mission(route, package_mass_kg, wind_speed_mps=0.0, wind_from_deg=0.0, params=None):
    """Estimate watt-hours by phase for flying a route out and back along the same legs.

    Returns the nominal total (package released, lighter return) and the required
    total, which assumes the contingency of returning with the package and adds
    the uncertainty allowance and reserve.
    """
    params = params or PLACEHOLDER_PARAMS
    loaded = _power_w(params["base_mass_kg"] + package_mass_kg, params)
    unloaded = _power_w(params["base_mass_kg"], params)
    altitude = route["cruise_altitude_m"]

    climb_s = altitude / params["climb_rate_mps"]
    descent_s = altitude / params["descent_rate_mps"]
    outbound_s = _legs_time_s(route["legs"], False, wind_speed_mps, wind_from_deg, params)
    return_s = _legs_time_s(route["legs"], True, wind_speed_mps, wind_from_deg, params)

    def wh(power_w, seconds):
        return power_w * seconds / 3600

    phases = {
        "takeoff_climb_wh": wh(loaded * params["climb_power_factor"], climb_s),
        "outbound_loaded_wh": wh(loaded, outbound_s),
        "placement_hover_wh": wh(loaded, params["placement_hover_s"]),
        "return_unloaded_wh": wh(unloaded, return_s + descent_s),
    }
    return_loaded_wh = wh(loaded, return_s + descent_s)
    nominal = sum(phases.values())
    contingency = nominal - phases["return_unloaded_wh"] + return_loaded_wh
    allowance = contingency * params["uncertainty_fraction"]
    return {
        "phases": phases,
        "return_loaded_wh": return_loaded_wh,
        "nominal_wh": nominal,
        "uncertainty_allowance_wh": allowance,
        "reserve_wh": params["reserve_wh"],
        "required_wh": contingency + allowance + params["reserve_wh"],
        "flight_time_s": climb_s + outbound_s + params["placement_hover_s"] + return_s + descent_s,
        "model": "placeholder-v0 (invented numbers)",
    }
