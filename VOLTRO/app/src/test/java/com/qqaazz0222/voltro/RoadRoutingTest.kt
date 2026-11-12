package com.qqaazz0222.voltro

import com.qqaazz0222.voltro.domain.model.*
import com.qqaazz0222.voltro.domain.usecase.*
import org.junit.Assert.*
import org.junit.Test

class RoadRoutingTest {
    private val start = GeoPoint(37.5665, 126.978)
    private val end = GeoPoint(37.58, 127.1)
    private val destination = Destination("test", "도착", "", end)
    private val direct = listOf(start, GeoPoint(37.57, 127.04), end)
    private val detour = listOf(start, GeoPoint(37.61, 127.04), end)
    private fun geometry(points: List<GeoPoint>, seconds: Double): RoadGeometry {
        val distances = points.zipWithNext().map { (a, b) -> a.distanceTo(b) }
        return RoadGeometry(distances.sum(), seconds, points, distances, distances.map { it / 10 })
    }
    @Test fun oneProviderRouteStaysOneAndUsesItsRoadDistance() {
        val g = geometry(direct, 1200.0)
        val routes = RoadRouteMapper.candidates(listOf(g), destination, VehicleEnergyState())
        assertEquals(1, routes.size)
        val r = routes.single()
        assertEquals(RouteSource.OSRM, r.source)
        assertEquals(g.distanceMeters / 1000 / 5.2, r.energyKwh, 1e-9)
        assertEquals(20.0, r.minutesAt(r.distanceKm), 1e-9)
        assertEquals(start, r.pointAt(0.0)); assertEquals(end, r.pointAt(r.distanceKm))
        val middle = r.nodes[1]
        assertEquals(middle.point, r.pointAt(middle.distanceKm))
        assertEquals(middle.elapsedMinutes!!, r.minutesAt(middle.distanceKm), 1e-9)
    }
    @Test fun alternativesAreDistinctAndLabelsFollowProviderMetrics() {
        val routes = RoadRouteMapper.candidates(listOf(geometry(detour, 900.0), geometry(direct, 1200.0), geometry(direct, 1200.0)), destination, VehicleEnergyState())
        assertEquals(2, routes.size)
        assertEquals(RouteType.FASTEST, routes.first().type)
        assertEquals(RouteType.ECO, routes.last().type)
        assertTrue(routes.last().energyKwh < routes.first().energyKwh)
        assertEquals(2, routes.map { it.id }.distinct().size)
    }
    @Test(expected = IllegalArgumentException::class) fun disconnectedDestinationRejected() {
        RoadRouteMapper.candidates(listOf(geometry(direct, 1200.0)), destination.copy(point = GeoPoint(0.0, 0.0)), VehicleEnergyState())
    }
    @Test(expected = IllegalArgumentException::class) fun geometryCannotClaimAnUnrelatedShortDistance() {
        val g = geometry(direct, 1200.0)
        RoadRouteMapper.candidates(listOf(g.copy(distanceMeters = 100.0, segmentMeters = listOf(50.0, 50.0))), destination, VehicleEnergyState())
    }
    @Test(expected = IllegalArgumentException::class) fun missingPerSegmentAnnotationsRejected() {
        RoadRouteMapper.candidates(listOf(geometry(direct, 1200.0).copy(segmentSeconds = emptyList())), destination, VehicleEnergyState())
    }
    @Test fun webMercatorKeepsSeoulAndKoreanCoastInTheCorrectPlace() {
        for (p in listOf(start, end, GeoPoint(38.1905, 128.6008))) {
            val xy = MapProjection.project(p); val decoded = MapProjection.unproject(xy.first, xy.second)
            assertEquals(p.latitude, decoded.latitude, 1e-9); assertEquals(p.longitude, decoded.longitude, 1e-9)
        }
        assertTrue(MapProjection.project(end).first > MapProjection.project(start).first)
        assertTrue(MapProjection.project(end).second < MapProjection.project(start).second)
    }
}
