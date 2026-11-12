package com.qqaazz0222.voltro

import com.qqaazz0222.voltro.domain.model.*
import com.qqaazz0222.voltro.domain.usecase.*
import org.junit.Assert.*
import org.junit.Test

class RoutingTest {
    private val vehicle = VehicleEnergyState()
    private fun route(type: RouteType, distance: Double, minutes: Double) = RouteCandidate(type.name, type, type.name, "Mock",
        distance, minutes, distance / 5.2, 68 - distance / 5.2 / 70 * 100, .9,
        listOf(RouteNode("seoul", GeoPoint(37.5665, 126.978), 0.0),
            RouteNode("hanam", GeoPoint(37.60, 127.10), 15.0),
            RouteNode("junction", GeoPoint(37.65, 127.40), 35.0),
            RouteNode(type.name, GeoPoint(if (type == RouteType.ECO) 37.95 else 37.48, 127.95), 80.0),
            RouteNode("end", GeoPoint(37.7644, 128.8995), distance)))
    private val fast = route(RouteType.FASTEST, 180.0, 130.0)
    private val eco = route(RouteType.ECO, 165.0, 145.0)
    @Test fun recommendationRespectsPolicy() {
        assertEquals(eco.id, RouteRecommendation.recommend(listOf(fast, eco), Preferences()))
        assertEquals(fast.id, RouteRecommendation.recommend(listOf(fast, eco), Preferences(maxExtraMinutes = 0.0)))
        assertNull(RouteRecommendation.recommend(listOf(fast, eco), Preferences(minArrivalSoc = 90.0)))
        assertEquals(fast.id, RouteRecommendation.recommend(listOf(fast, eco.copy(energyKwh = fast.energyKwh)), Preferences()))
        assertNull(RouteRecommendation.recommend(emptyList(), Preferences()))
    }
    @Test fun sharedPrefixAndJunctionEnergy() {
        val junction = JunctionAnalyzer.divergence(fast, eco)!!
        assertEquals("junction", junction.node.id)
        assertNull(JunctionAnalyzer.divergence(fast, fast))
        val point = fast.pointAt(33.8)
        val soc = 68 - 33.8 / 5.2 / 70 * 100
        val advice = JunctionAnalyzer.evaluate(fast, eco, point, 5.0, vehicle, soc, Preferences(), true)!!
        assertEquals(1200.0, advice.distanceMeters, .01)
        assertEquals(15.0 / 5.2, advice.savingKwh, .000001)
        assertEquals(15.0, advice.additionalMinutes, .000001)
        assertEquals(eco.arrivalSoc, advice.arrivalSoc, .000001)
        assertNull(JunctionAnalyzer.evaluate(fast, eco, point, 100.0, vehicle, soc, Preferences(), true))
        assertNull(JunctionAnalyzer.evaluate(fast, eco, point, 5.0, vehicle, soc, Preferences(), false))
        assertNull(JunctionAnalyzer.evaluate(fast, eco, fast.pointAt(35.1), 5.0, vehicle, soc, Preferences(), true))
        assertNull(JunctionAnalyzer.evaluate(fast, eco, GeoPoint(0.0, 0.0), 5.0, vehicle, soc, Preferences(), true))
        assertNull(JunctionAnalyzer.evaluate(eco, fast, point, 5.0, vehicle, soc, Preferences(), true))
    }
    @Test fun positionAndTimeRemainContinuousAtSwitch() {
        assertEquals(fast.pointAt(33.8), eco.pointAt(33.8))
        assertEquals(fast.minutesAt(33.8), eco.minutesAt(33.8), .000001)
        assertEquals(145.0, fast.minutesAt(33.8) + eco.durationMinutes - eco.minutesAt(33.8), .000001)
    }
    @Test(expected = IllegalArgumentException::class) fun invalidLocationRejected() { GeoPoint(91.0, 0.0) }
}
