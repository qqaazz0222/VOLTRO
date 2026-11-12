package com.qqaazz0222.voltro

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.qqaazz0222.voltro.data.pleos.PleosVehicleRepository
import com.qqaazz0222.voltro.domain.model.*
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

/** Opt-in real SDK test; run only on Pleos Connect with Vehicle Service available. */
@RunWith(AndroidJUnit4::class)
class PleosVehicleIntegrationTest {
    @Test fun readsBatteryThroughVehicleSdkWithoutInventingCapacity() = runBlocking {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val profile = VehicleEnergyState(usableBatteryCapacityKwh = 70.0)
        val repository = PleosVehicleRepository(context, profile)
        val started = System.currentTimeMillis()
        val vehicle = repository.getVehicleEnergyState()
        assertEquals(DataSource.PLEOS, vehicle.source)
        assertTrue(vehicle.socPercent in 0.0..100.0)
        assertTrue(vehicle.timestamp >= started)
        assertTrue(vehicle.efficiencyKmPerKwh > 0)
        assertEquals(70.0, vehicle.usableBatteryCapacityKwh, 0.0)
        assertEquals(DataSource.MOCK, vehicle.capacitySource)
        assertEquals(vehicle, repository.observeVehicleEnergyState().value)
    }
}
