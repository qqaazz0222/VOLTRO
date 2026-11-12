from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.models import EnergyRequest, CompareRequest, JunctionRequest, CompleteRequest
from app.junctions import evaluate
from app.trips import complete_trip
from app.energy import MODEL_VERSION, predict_energy, arrival_soc
from app.routing import MockRouteProvider
from threading import RLock
from time import monotonic
from uuid import uuid4

app = FastAPI(title="VOLTRO API", version="0.1.0")
provider = MockRouteProvider()
sessions: dict = {}
session_lock = RLock()


@app.exception_handler(StarletteHTTPException)
async def http_error(_request, exc):
    return JSONResponse(status_code=exc.status_code, content={"error": {
        "code": {404: "NOT_FOUND", 409: "INVALID_STATE", 422: "INVALID_INPUT", 429: "RATE_LIMITED"}.get(exc.status_code, "REQUEST_FAILED"),
        "message": str(exc.detail), "retryable": exc.status_code in (429, 503)}})


@app.get("/api/v1/destinations")
def destinations():
    return {"destinations": provider.destinations(), "source": "MOCK"}


@app.post("/api/v1/routes/compare")
def compare(body: CompareRequest):
    try:
        result = provider.compare(body.origin, body.destination, body.vehicle, body.preferences)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    trip_id = str(uuid4())
    result["trip_id"] = trip_id
    with session_lock:
        for key in list(sessions):
            if monotonic() - sessions[key]["created"] > 7200:
                del sessions[key]
        if len(sessions) >= 1000:
            raise HTTPException(429, "데모 세션이 가득 찼습니다. 나중에 다시 시도하세요.")
        sessions[trip_id] = {"created": monotonic(), "comparison": result, "request": body, "notified": set(), "completed": False}
    return result


@app.post("/api/v1/junctions/evaluate")
def junction_evaluate(body: JunctionRequest):
    with session_lock:
        session = sessions.get(body.trip_id)
        if not session or monotonic() - session["created"] > 7200:
            raise HTTPException(404, "주행 세션을 찾을 수 없습니다. 경로를 다시 분석하세요.")
        if session["completed"]:
            raise HTTPException(409, "이미 종료된 주행입니다.")
        routes = session["comparison"]["routes"]
        current = next((r for r in routes if r["route_id"] == body.active_route_id), None)
        if current is None:
            raise HTTPException(422, "세션에 포함되지 않은 경로입니다.")
        choices = [evaluate(current, other, body.location, body.current_soc_percent,
                            session["request"].vehicle, session["request"].preferences,
                            body.accuracy_meters, body.navigation_selectable)
                   for other in routes if other != current]
        choices = [r for r in choices if r is not None]
        if not choices:
            return {"should_notify": False, "source": "MOCK"}
        advice = max(choices, key=lambda r: r["energy_saving_kwh"])
        key = (body.active_route_id, advice["junction_id"])
        if key in session["notified"]:
            return dict(advice, should_notify=False, reason="ALREADY_NOTIFIED")
        session["notified"].add(key)
        return advice


@app.post("/api/v1/trips/complete")
def trips_complete(body: CompleteRequest):
    # Accept retries after server restart; the persisted idempotency record is authoritative.
    with session_lock:
        result = complete_trip(body)
        if body.trip_id in sessions:
            sessions[body.trip_id]["completed"] = True
        return result


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
