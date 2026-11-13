package com.qqaazz0222.voltro

import com.qqaazz0222.voltro.domain.model.*
import com.qqaazz0222.voltro.domain.usecase.*
import org.junit.Assert.*
import org.junit.Test

class RouteInsightsTest {
    private val vehicle = VehicleEnergyState()
    private fun route(distance: Double = 165.0) = RouteCandidate("eco", RouteType.ECO, "ECO", "test", distance,
        145.0, distance / 5.2, 68 - distance / 5.2 / 70 * 100, .9,
        listOf(RouteNode("a", GeoPoint(37.0, 127.0), 0.0), RouteNode("b", GeoPoint(38.0, 128.0), distance)))
    @Test fun departureThresholdPreservesMinimumReserveExactly() {
        val route = route()
        val insight = route.insights(vehicle, Preferences(), route)
        assertEquals(15.0, EnergyEngine.arrivalSoc(insight.requiredDepartureSoc, 70.0, route.energyKwh), 1e-9)
        assertEquals(0.0, insight.additionalChargeKwh, 1e-9)
        assertEquals(route.arrivalSoc - 15, insight.reserveMarginSoc, 1e-9)
    }
    @Test fun insufficientChargeUsesBatteryEnergyAndNeverHidesUnreachableRoute() {
        val low = vehicle.copy(socPercent = 20.0)
        val route = route().copy(arrivalSoc = 20 - route().energyKwh / 70 * 100)
        val insight = route.insights(low, Preferences(), route)
        assertEquals(route.energyKwh + .15 * 70 - .20 * 70, insight.additionalChargeKwh, 1e-9)
        assertTrue(insight.reachableWithFullBattery)
        val long = route(600.0)
        assertFalse(long.insights(vehicle, Preferences(), long).reachableWithFullBattery)
        assertTrue(long.insights(vehicle, Preferences(), long).requiredDepartureSoc > 100)
    }
    @Test fun lowerEfficiencyRaisesConsumptionByTwentyFivePercent() {
        val route = route()
        val insight = route.insights(vehicle, Preferences(), route)
        assertEquals(68 - (165 / (5.2 * .8)) / 70 * 100, insight.lowerEfficiencyArrivalSoc, 1e-9)
        assertTrue(insight.lowerEfficiencyArrivalSoc < route.arrivalSoc)
        assertEquals(route.arrivalSoc, route.insights(vehicle, Preferences(), route, 0.0).lowerEfficiencyArrivalSoc, 1e-9)
    }
    @Test(expected = IllegalArgumentException::class)
    fun invalidSensitivityCannotProduceInfiniteEnergy() { route().insights(vehicle, Preferences(), route(), 1.0) }
}
