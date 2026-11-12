package com.qqaazz0222.voltro.domain.usecase

import com.qqaazz0222.voltro.domain.model.*

data class DrivingMetrics(val currentSoc: Double, val remainingKm: Double, val remainingMinutes: Double, val arrivalSoc: Double)

fun DrivingState.metrics(vehicle: VehicleEnergyState): DrivingMetrics {
    val remaining = (activeRoute.distanceKm - distanceKm).coerceAtLeast(0.0)
    val soc = EnergyEngine.arrivalSoc(vehicle.socPercent, vehicle.usableBatteryCapacityKwh, consumedKwh)
    return DrivingMetrics(soc, remaining, (activeRoute.durationMinutes - activeRoute.minutesAt(distanceKm)).coerceAtLeast(0.0),
        EnergyEngine.arrivalSoc(soc.coerceIn(0.0, 100.0), vehicle.usableBatteryCapacityKwh,
            EnergyEngine.predict(remaining, vehicle.efficiencyKmPerKwh)))
}
