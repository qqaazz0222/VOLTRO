import math

MODEL_VERSION = "baseline-1.0"


def predict_energy(distance_km: float, efficiency_km_per_kwh: float) -> float:
    if not all(math.isfinite(x) for x in (distance_km, efficiency_km_per_kwh)):
        raise ValueError("Inputs must be finite")
    if distance_km < 0 or efficiency_km_per_kwh <= 0:
        raise ValueError("Distance must be nonnegative and efficiency positive")
    return distance_km / efficiency_km_per_kwh


def arrival_soc(current_soc: float, capacity_kwh: float, energy_kwh: float) -> float:
    if not all(math.isfinite(x) for x in (current_soc, capacity_kwh, energy_kwh)):
        raise ValueError("Inputs must be finite")
    if not 0 <= current_soc <= 100 or capacity_kwh <= 0 or energy_kwh < 0:
        raise ValueError("Invalid battery state")
    # Keep negative results: an infeasible trip must never look reachable.
    return current_soc - energy_kwh / capacity_kwh * 100
