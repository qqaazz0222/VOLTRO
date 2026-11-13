package com.qqaazz0222.voltro.domain.usecase

import com.qqaazz0222.voltro.domain.model.*
import kotlin.math.max

data class RouteInsights(
    val requiredDepartureSoc: Double,
    val additionalChargeKwh: Double,
    val reserveMarginSoc: Double,
    val lowerEfficiencyArrivalSoc: Double,
    val savingKwh: Double,
    val extraMinutes: Double,
) {
    val reachableWithFullBattery get() = requiredDepartureSoc <= 100.0 + 1e-9
}

/** Sensitivity is an explicit what-if assumption, never a confidence interval. */
fun RouteCandidate.insights(vehicle: VehicleEnergyState, preferences: Preferences,
                            fastest: RouteCandidate, efficiencyDrop: Double = .20): RouteInsights {
    require(efficiencyDrop.isFinite() && efficiencyDrop in 0.0..<1.0)
    val required = preferences.minArrivalSoc + energyKwh / vehicle.usableBatteryCapacityKwh * 100
    return RouteInsights(required,
        max(0.0, (required - vehicle.socPercent) / 100 * vehicle.usableBatteryCapacityKwh),
        arrivalSoc - preferences.minArrivalSoc,
        EnergyEngine.arrivalSoc(vehicle.socPercent, vehicle.usableBatteryCapacityKwh, energyKwh / (1 - efficiencyDrop)),
        fastest.energyKwh - energyKwh, durationMinutes - fastest.durationMinutes)
}
