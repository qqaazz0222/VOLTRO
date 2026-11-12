import math
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.energy import predict_energy, arrival_soc


def test_baseline():
    assert predict_energy(120, 5) == 24
    assert arrival_soc(68, 70, 24) == pytest.approx(33.714285714)
    assert predict_energy(0, 5) == 0
    assert arrival_soc(10, 70, 24) < 0


@pytest.mark.parametrize("distance,efficiency", [(-1, 5), (1, 0), (1, -1), (math.nan, 5), (1, math.inf)])
def test_invalid_energy(distance, efficiency):
    with pytest.raises(ValueError):
        predict_energy(distance, efficiency)


@pytest.mark.parametrize("soc,capacity,energy", [(101, 70, 1), (-1, 70, 1), (68, 0, 1), (68, 70, -1)])
def test_invalid_battery(soc, capacity, energy):
    with pytest.raises(ValueError):
        arrival_soc(soc, capacity, energy)


def test_prediction_api():
    client = TestClient(app)
    body = dict(distance_km=120, efficiency_km_per_kwh=5, current_soc_percent=68, usable_capacity_kwh=70)
    assert client.post("/api/v1/energy/predict", json=body).json()["estimated_energy_kwh"] == 24
    body["usable_capacity_kwh"] = 0
    response = client.post("/api/v1/energy/predict", json=body)
    assert response.status_code == 422
    assert response.json()["error"]["retryable"] is False
