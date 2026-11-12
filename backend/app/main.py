from fastapi import FastAPI

app = FastAPI(title="VOLTRO API", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok", "mode": "mock", "model_version": "baseline-1.0"}


@app.get("/api/v1/vehicle")
def vehicle():
    return {"soc_percent": 68.0, "efficiency_km_per_kwh": 5.2,
            "usable_capacity_kwh": 70.0, "source": "MOCK"}
