from pydantic import BaseModel, ConfigDict, Field
from typing import Literal


class Model(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, extra="forbid")


class EnergyRequest(Model):
    distance_km: float = Field(ge=0, le=10000)
    efficiency_km_per_kwh: float = Field(gt=0, le=30)
    current_soc_percent: float = Field(ge=0, le=100)
    usable_capacity_kwh: float = Field(gt=0, le=300)


class Point(Model):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class Vehicle(Model):
    soc_percent: float = Field(default=68, ge=0, le=100)
    usable_capacity_kwh: float = Field(default=70, gt=0, le=300)
    efficiency_km_per_kwh: float = Field(default=5.2, gt=0, le=30)


class Preferences(Model):
    min_arrival_soc_percent: float = Field(default=15, ge=0, le=100)
    max_extra_minutes: float = Field(default=15, ge=0, le=120)
    min_energy_saving_kwh: float = Field(default=1, ge=0, le=100)


class CompareRequest(Model):
    origin: Point
    destination: Point
    vehicle: Vehicle = Field(default_factory=Vehicle)
    preferences: Preferences = Field(default_factory=Preferences)


class JunctionRequest(Model):
    trip_id: str = Field(min_length=1, max_length=100)
    active_route_id: str = Field(min_length=1, max_length=100)
    location: Point
    current_soc_percent: float = Field(ge=0, le=100)
    accuracy_meters: float = Field(default=5, ge=0)
    navigation_selectable: bool = False


class CompleteRequest(Model):
    trip_id: str = Field(min_length=1, max_length=100)
    estimated_energy_kwh: float = Field(ge=0, le=1000)
    actual_energy_kwh: float | None = Field(default=None, ge=0, le=1000)
    simulated_energy_kwh: float | None = Field(default=None, ge=0, le=1000)
    distance_km: float = Field(ge=0, le=10000)
    duration_minutes: float = Field(ge=0, le=10000)
    energy_source: Literal["MEASURED", "MOCK_SOC_ESTIMATE"] = "MOCK_SOC_ESTIMATE"
