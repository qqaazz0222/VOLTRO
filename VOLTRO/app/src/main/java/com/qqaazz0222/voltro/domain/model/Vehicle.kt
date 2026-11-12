package com.qqaazz0222.voltro.domain.model

enum class DataSource { PLEOS, MOCK, USER_INPUT }

data class VehicleEnergyState(
    val socPercent: Double = 68.0,
    val efficiencyKmPerKwh: Double = 5.2,
    val usableBatteryCapacityKwh: Double = 70.0,
    val isCharging: Boolean = false,
    val timestamp: Long = System.currentTimeMillis(),
    val source: DataSource = DataSource.MOCK,
) {
    init {
        require(socPercent.isFinite() && socPercent in 0.0..100.0)
        require(efficiencyKmPerKwh.isFinite() && efficiencyKmPerKwh > 0)
        require(usableBatteryCapacityKwh.isFinite() && usableBatteryCapacityKwh > 0)
    }
}
