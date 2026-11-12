from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_and_vehicle():
    assert client.get("/health").json()["status"] == "ok"
    vehicle = client.get("/api/v1/vehicle").json()
    assert vehicle["soc_percent"] == 68
    assert vehicle["efficiency_km_per_kwh"] == 5.2
