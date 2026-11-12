package com.qqaazz0222.voltro.domain.repository

import com.qqaazz0222.voltro.domain.model.VehicleEnergyState
import kotlinx.coroutines.flow.StateFlow

interface VehicleDataRepository {
    suspend fun getVehicleEnergyState(): VehicleEnergyState
    fun observeVehicleEnergyState(): StateFlow<VehicleEnergyState>
}
