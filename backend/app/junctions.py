import math
from app.models import Point, Preferences, Vehicle
from app.energy import predict_energy, arrival_soc


def divergence(current: dict, alternative: dict):
    count = 0
    for a, b in zip(current["nodes"], alternative["nodes"]):
        if a["node_id"] != b["node_id"] or a["latitude"] != b["latitude"] or a["longitude"] != b["longitude"]:
            break
        count += 1
    if not count or count == min(len(current["nodes"]), len(alternative["nodes"])):
        return None
    return current["nodes"][count - 1], alternative["nodes"][count - 1]


def match(route: dict, point: Point):
    scale_x = 111320 * math.cos(math.radians(point.latitude))
    candidates = []
    for a, b in zip(route["nodes"], route["nodes"][1:]):
        ax, ay = (a["longitude"] - point.longitude) * scale_x, (a["latitude"] - point.latitude) * 111320
        dx, dy = (b["longitude"] - a["longitude"]) * scale_x, (b["latitude"] - a["latitude"]) * 111320
        length = dx * dx + dy * dy
        t = max(0, min(1, -(ax * dx + ay * dy) / length)) if length else 0
        candidates.append((a["distance_km"] + (b["distance_km"] - a["distance_km"]) * t,
                           math.hypot(ax + t * dx, ay + t * dy)))
    return min(candidates, key=lambda pair: pair[1])


def minutes_at(route: dict, km: float):
    split = route["nodes"][2]["distance_km"]
    prefix_minutes = min(25, route["eta_minutes"] / 2)
    return prefix_minutes * km / split if km <= split else (
        prefix_minutes + (route["eta_minutes"] - prefix_minutes) * (km - split) / (route["distance_km"] - split))


def evaluate(current: dict, alternative: dict, location: Point, current_soc: float, vehicle: Vehicle,
             preferences: Preferences, accuracy_meters: float, navigation_selectable: bool):
    junction = divergence(current, alternative)
    if not junction or not navigation_selectable or accuracy_meters > 50:
        return None
    a, b = junction
    along, offset = match(current, location)
    remaining = (a["distance_km"] - along) * 1000
    if offset > 75 or not 1 <= remaining <= 1500 or min(current["confidence"], alternative["confidence"]) < .8:
        return None
    energy_current = predict_energy(current["distance_km"] - a["distance_km"], vehicle.efficiency_km_per_kwh)
    energy_alternative = predict_energy(alternative["distance_km"] - b["distance_km"], vehicle.efficiency_km_per_kwh)
    saving = energy_current - energy_alternative
    extra = (alternative["eta_minutes"] - minutes_at(alternative, b["distance_km"])) - (
        current["eta_minutes"] - minutes_at(current, a["distance_km"]))
    arrival = arrival_soc(current_soc, vehicle.usable_capacity_kwh, predict_energy(
        alternative["distance_km"] - b["distance_km"] + remaining / 1000, vehicle.efficiency_km_per_kwh))
    if saving <= 0 or saving < preferences.min_energy_saving_kwh or extra > preferences.max_extra_minutes + 1e-9 or arrival < preferences.min_arrival_soc_percent:
        return None
    return {"junction_id": a["node_id"], "distance_meters": remaining,
            "alternative_route_id": alternative["route_id"], "current_remaining_energy_kwh": energy_current,
            "alternative_remaining_energy_kwh": energy_alternative, "energy_saving_kwh": saving,
            "additional_minutes": extra, "alternative_arrival_soc_percent": arrival,
            "confidence": min(current["confidence"], alternative["confidence"]),
            "navigation_selectable": True, "should_notify": True, "source": "MOCK"}
