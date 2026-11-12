package com.qqaazz0222.voltro.domain.usecase

object EnergyEngine {
    fun predict(distanceKm: Double, efficiencyKmPerKwh: Double): Double {
        require(distanceKm.isFinite() && distanceKm >= 0)
        require(efficiencyKmPerKwh.isFinite() && efficiencyKmPerKwh > 0)
        return distanceKm / efficiencyKmPerKwh
    }

    fun arrivalSoc(soc: Double, capacityKwh: Double, energyKwh: Double): Double {
        require(soc.isFinite() && soc in 0.0..100.0)
        require(capacityKwh.isFinite() && capacityKwh > 0)
        require(energyKwh.isFinite() && energyKwh >= 0)
        return soc - energyKwh / capacityKwh * 100
    }
}
