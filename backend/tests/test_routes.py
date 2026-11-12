import pytest
from fastapi.testclient import TestClient
from app.main import app, provider
from app.routing import recommend
from app.models import Preferences

client = TestClient(app)


def compare_body():
    return {"origin": {"latitude": 37.5665, "longitude": 126.9780},
            "destination": {"latitude": 37.7644, "longitude": 128.8995},
            "vehicle": {"soc_percent": 68, "usable_capacity_kwh": 70, "efficiency_km_per_kwh": 5.2}}


def test_compare_consistency():
    result = client.post("/api/v1/routes/compare", json=compare_body()).json()
    assert len(result["routes"]) == 3
    assert result["recommended_route_id"] == "gangneung_eco"
    assert result["source"] == "MOCK"
    assert result["trip_id"]
    for route in result["routes"]:
        assert route["energy_kwh"] == pytest.approx(route["distance_km"] / 5.2)
        assert route["arrival_soc_percent"] == pytest.approx(68 - route["energy_kwh"] / 70 * 100)
        assert route["nodes"][-1]["distance_km"] == route["distance_km"]


def test_preferences_and_no_safe_route():
    body = compare_body()
    body["preferences"] = {"max_extra_minutes": 0}
    assert client.post("/api/v1/routes/compare", json=body).json()["recommended_route_id"] == "gangneung_fastest"
    body["vehicle"]["soc_percent"] = 20
    assert client.post("/api/v1/routes/compare", json=body).json()["recommended_route_id"] is None


def test_mock_rejects_unknown_destination_and_origin():
    body = compare_body()
    body["destination"]["latitude"] = 0
    assert client.post("/api/v1/routes/compare", json=body).status_code == 422
    body = compare_body()
    body["origin"]["latitude"] = 0
    assert client.post("/api/v1/routes/compare", json=body).status_code == 422


def test_all_destinations_consistent():
    for destination in provider.destinations():
        body = compare_body()
        body["destination"] = {key: destination[key] for key in ("latitude", "longitude")}
        result = client.post("/api/v1/routes/compare", json=body)
        assert result.status_code == 200
        assert len(result.json()["routes"]) >= 2


def test_equal_energy_does_not_claim_savings():
    routes = [dict(route_id="b", eta_minutes=10, energy_kwh=2, arrival_soc_percent=50, confidence=.9),
              dict(route_id="a", eta_minutes=15, energy_kwh=2, arrival_soc_percent=50, confidence=.9)]
    assert recommend(routes, Preferences()) == "b"
