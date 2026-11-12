package com.qqaazz0222.voltro

import com.qqaazz0222.voltro.data.mock.MockVehicleRepository
import com.qqaazz0222.voltro.domain.model.DataSource
import com.qqaazz0222.voltro.domain.model.VehicleEnergyState
import org.junit.Assert.*
import org.junit.Test

class VehicleTest {
    @Test fun mockVehicleHasValidEnergyState() {
        val state = MockVehicleRepository().observeVehicleEnergyState().value
        assertEquals(68.0, state.socPercent, 0.0)
        assertEquals(5.2, state.efficiencyKmPerKwh, 0.0)
        assertEquals(DataSource.MOCK, state.source)
    }
    @Test(expected = IllegalArgumentException::class)
    fun invalidSocRejected() { VehicleEnergyState(socPercent = 101.0) }
}
