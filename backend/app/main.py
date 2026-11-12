from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.models import EnergyRequest
from app.energy import MODEL_VERSION, predict_energy, arrival_soc

app = FastAPI(title="VOLTRO API", version="0.1.0")


@app.exception_handler(RequestValidationError)
async def invalid_request(_request, _exc):
    return JSONResponse(status_code=422, content={"error": {
        "code": "INVALID_INPUT", "message": "입력 범위와 필수 항목을 확인하세요.", "retryable": False}})


@app.post("/api/v1/energy/predict")
def energy_predict(body: EnergyRequest):
    energy = predict_energy(body.distance_km, body.efficiency_km_per_kwh)
    return {"estimated_energy_kwh": energy,
            "estimated_arrival_soc_percent": arrival_soc(body.current_soc_percent, body.usable_capacity_kwh, energy),
            "model_version": MODEL_VERSION}


@app.get("/health")
def health():
    return {"status": "ok", "mode": "mock", "model_version": "baseline-1.0"}


@app.get("/api/v1/vehicle")
def vehicle():
    return {"soc_percent": 68.0, "efficiency_km_per_kwh": 5.2,
            "usable_capacity_kwh": 70.0, "source": "MOCK"}
