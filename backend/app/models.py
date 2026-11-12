from pydantic import BaseModel, ConfigDict, Field


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
