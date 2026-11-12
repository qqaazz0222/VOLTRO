import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from app.energy import MODEL_VERSION, predict_energy, arrival_soc
from app.models import Point, Vehicle, Preferences

SCENARIO_PATH = Path(os.environ.get("VOLTRO_SCENARIO", Path(__file__).resolve().parents[2] / "mock-data" / "scenario.json"))


class MockRouteProvider:
    """Synthetic graph for demonstration. Not a public-road routing service."""

    def __init__(self):
        self.scenario = json.loads(SCENARIO_PATH.read_text())

    def destinations(self):
        return self.scenario["destinations"]

    def compare(self, origin: Point, destination: Point, vehicle: Vehicle, preferences: Preferences):
        expected = Point(**self.scenario["origin"])
        if distance_meters(origin, expected) > 1000:
            raise ValueError("Mock 출발지는 서울 시청 주변으로 제한됩니다.")
        target = next((d for d in self.destinations() if distance_meters(destination, Point(
            latitude=d["latitude"], longitude=d["longitude"])) < 100), None)
        if target is None:
            raise ValueError("Mock 모드에서는 제공된 데모 목적지를 선택하세요.")
        routes = []
        for template in self.scenario["routes"]:
            distance = template["distance_km"] * target["distance_scale"]
            energy = predict_energy(distance, vehicle.efficiency_km_per_kwh)
            nodes = [dict(n) for n in self.scenario["common_nodes"]]
            for i, point in enumerate(template["via"]):
                nodes.append(dict(point, node_id=f'{template["route_type"]}_{i}',
                                  distance_km=35 + (distance - 35) * (i + 1) / 3))
            nodes.append(dict(latitude=target["latitude"], longitude=target["longitude"],
                              node_id=target["id"], distance_km=distance))
            routes.append({
                "route_id": f'{target["id"]}_{template["route_type"].lower()}',
                "route_type": template["route_type"], "label": template["label"],
                "road_name": template["road_name"], "distance_km": distance,
                "eta_minutes": template["eta_minutes"] * target["distance_scale"],
                "energy_kwh": energy,
                "arrival_soc_percent": arrival_soc(vehicle.soc_percent, vehicle.usable_capacity_kwh, energy),
                "confidence": 0.9, "nodes": nodes,
                "polyline": [{"latitude": n["latitude"], "longitude": n["longitude"]} for n in nodes],
            })
        return {"routes": routes, "recommended_route_id": recommend(routes, preferences),
                "destination_name": target["name"], "provider": self.scenario["provider"],
                "calculated_at": datetime.now(timezone.utc).isoformat(), "model_version": MODEL_VERSION,
                "source": "MOCK", "scenario_version": self.scenario["version"]}


def recommend(routes: list[dict], preferences: Preferences) -> str | None:
    fastest = min(routes, key=lambda r: (r["eta_minutes"], r["energy_kwh"], r["route_id"]))
    safe = [r for r in routes if r["arrival_soc_percent"] >= preferences.min_arrival_soc_percent
            and r["confidence"] >= 0.8
            and r["eta_minutes"] - fastest["eta_minutes"] <= preferences.max_extra_minutes]
    if not safe:
        return None
    eco = min(safe, key=lambda r: (r["energy_kwh"], r["eta_minutes"], r["route_id"]))
    if fastest["energy_kwh"] - eco["energy_kwh"] >= preferences.min_energy_saving_kwh:
        return eco["route_id"]
    # A safe fastest route remains selectable without claiming energy savings.
    return fastest["route_id"] if fastest in safe else None


def distance_meters(a: Point, b: Point) -> float:
    lat1, lat2 = math.radians(a.latitude), math.radians(b.latitude)
    dlat, dlon = lat2 - lat1, math.radians(b.longitude - a.longitude)
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371000 * 2 * math.asin(min(1, math.sqrt(h)))
