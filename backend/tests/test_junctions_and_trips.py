import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.junctions import divergence
from test_routes import compare_body

client = TestClient(app)


@pytest.fixture(autouse=True)
def local_db(tmp_path, monkeypatch):
    monkeypatch.setenv("VOLTRO_DB", str(tmp_path / "test.db"))


def junction_body(comparison, km=33.8):
    t = (km - 15) / 20
    return {"trip_id": comparison["trip_id"], "active_route_id": "gangneung_fastest",
            "location": {"latitude": 37.60 + .05 * t, "longitude": 127.10 + .30 * t},
            "current_soc_percent": 68 - km / 5.2 / 70 * 100, "navigation_selectable": True}


def test_shared_prefix_saving_and_deduplication():
    comparison = client.post("/api/v1/routes/compare", json=compare_body()).json()
    fast, _, eco = comparison["routes"]
    assert divergence(fast, eco)[0]["node_id"] == "junction-east"
    body = junction_body(comparison)
    response = client.post("/api/v1/junctions/evaluate", json=body).json()
    assert response["should_notify"]
    assert response["energy_saving_kwh"] == pytest.approx(15 / 5.2)
    assert response["distance_meters"] == pytest.approx(1200)
    assert response["additional_minutes"] == pytest.approx(15)
    assert response["alternative_arrival_soc_percent"] == pytest.approx(68 - 165 / 5.2 / 70 * 100)
    assert not client.post("/api/v1/junctions/evaluate", json=body).json()["should_notify"]
    body["active_route_id"] = "gangneung_eco"
    assert not client.post("/api/v1/junctions/evaluate", json=body).json()["should_notify"]


@pytest.mark.parametrize("override", [{"navigation_selectable": False}, {"accuracy_meters": 100},
                                      {"current_soc_percent": 10}, {"location": {"latitude": 38, "longitude": 127}}])
def test_unsafe_or_unavailable_advice_suppressed(override):
    comparison = client.post("/api/v1/routes/compare", json=compare_body()).json()
    body = junction_body(comparison) | override
    assert not client.post("/api/v1/junctions/evaluate", json=body).json()["should_notify"]


def test_far_away_passed_and_identical_routes():
    comparison = client.post("/api/v1/routes/compare", json=compare_body()).json()
    assert divergence(comparison["routes"][0], comparison["routes"][0]) is None
    assert not client.post("/api/v1/junctions/evaluate", json=junction_body(comparison, 20)).json()["should_notify"]
    body = junction_body(comparison)
    body["location"] = {"latitude": 37.65, "longitude": 127.40}
    assert not client.post("/api/v1/junctions/evaluate", json=body).json()["should_notify"]


def test_trip_completion_is_persistent_idempotent_and_not_measured():
    comparison = client.post("/api/v1/routes/compare", json=compare_body()).json()
    body = {"trip_id": comparison["trip_id"], "estimated_energy_kwh": 165 / 5.2,
            "simulated_energy_kwh": 165 / 5.2, "distance_km": 165, "duration_minutes": 145}
    result = client.post("/api/v1/trips/complete", json=body)
    assert result.status_code == 200
    assert result.json()["prediction_error_kwh"] is None
    assert result.json()["prediction_error_percent"] is None
    assert client.post("/api/v1/trips/complete", json=body).json() == result.json()
    body["distance_km"] = 170
    assert client.post("/api/v1/trips/complete", json=body).status_code == 409
    assert client.post("/api/v1/junctions/evaluate", json=junction_body(comparison)).status_code == 409


def test_mock_cannot_be_saved_as_measured():
    body = {"trip_id": "x", "estimated_energy_kwh": 20, "actual_energy_kwh": 21,
            "distance_km": 100, "duration_minutes": 60}
    assert client.post("/api/v1/trips/complete", json=body).status_code == 422
    body["energy_source"] = "MEASURED"
    result = client.post("/api/v1/trips/complete", json=body).json()
    assert result["prediction_error_kwh"] == 1
    assert result["prediction_error_percent"] == 5


def test_bad_session_and_location_validation():
    comparison = client.post("/api/v1/routes/compare", json=compare_body()).json()
    body = junction_body(comparison)
    body["trip_id"] = "unknown"
    assert client.post("/api/v1/junctions/evaluate", json=body).status_code == 404
    body["location"]["latitude"] = 91
    assert client.post("/api/v1/junctions/evaluate", json=body).status_code == 422
