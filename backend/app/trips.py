import json
import os
import sqlite3
from pathlib import Path
from fastapi import HTTPException
from app.models import CompleteRequest


def complete_trip(body: CompleteRequest):
    if body.energy_source == "MOCK_SOC_ESTIMATE" and body.actual_energy_kwh is not None:
        raise HTTPException(422, "Mock 소비량을 실측값으로 저장할 수 없습니다.")
    if body.energy_source == "MEASURED" and body.actual_energy_kwh is None:
        raise HTTPException(422, "실측 에너지 값이 필요합니다.")
    error = None if body.actual_energy_kwh is None else body.actual_energy_kwh - body.estimated_energy_kwh
    result = {"trip_id": body.trip_id, "status": "COMPLETED", "prediction_error_kwh": error,
              "prediction_error_percent": None if error is None or body.estimated_energy_kwh == 0 else error / body.estimated_energy_kwh * 100,
              "energy_source": body.energy_source}
    path = Path(os.environ.get("VOLTRO_DB", Path(__file__).resolve().parents[1] / "voltro.db"))
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE IF NOT EXISTS trips (id TEXT PRIMARY KEY, payload TEXT NOT NULL, response TEXT NOT NULL)")
        previous = db.execute("SELECT payload, response FROM trips WHERE id = ?", (body.trip_id,)).fetchone()
        payload = body.model_dump_json()
        if previous:
            if previous[0] != payload:
                raise HTTPException(409, "동일한 주행 ID에 서로 다른 결과가 있습니다.")
            return json.loads(previous[1])
        db.execute("INSERT INTO trips VALUES (?, ?, ?)", (body.trip_id, payload, json.dumps(result)))
    return result
