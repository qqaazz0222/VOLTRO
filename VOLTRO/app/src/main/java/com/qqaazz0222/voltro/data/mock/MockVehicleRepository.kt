package com.qqaazz0222.voltro.data.mock

import com.qqaazz0222.voltro.domain.model.VehicleEnergyState
import com.qqaazz0222.voltro.domain.repository.VehicleDataRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

class MockVehicleRepository : VehicleDataRepository {
    private val state = MutableStateFlow(VehicleEnergyState())
    override suspend fun getVehicleEnergyState() = state.value
    override fun observeVehicleEnergyState() = state.asStateFlow()
}
