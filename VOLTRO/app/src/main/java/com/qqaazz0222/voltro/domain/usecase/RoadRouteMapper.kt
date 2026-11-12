package com.qqaazz0222.voltro.domain.usecase

import com.qqaazz0222.voltro.domain.model.*
import kotlin.math.*

data class RoadGeometry(val distanceMeters: Double, val durationSeconds: Double, val points: List<GeoPoint>,
                        val segmentMeters: List<Double>, val segmentSeconds: List<Double>)

/** Converts verified provider geometry; never invents alternatives or straight-line road routes. */
object RoadRouteMapper {
    fun candidates(raw: List<RoadGeometry>, destination: Destination, vehicle: VehicleEnergyState): List<RouteCandidate> {
        require(raw.size in 1..3) { "도로 경로 개수가 올바르지 않습니다." }
        val valid = raw.distinctBy { it.points }.sortedBy { it.durationSeconds }
        val shortest = valid.indices.minBy { valid[it].distanceMeters }
        return valid.mapIndexed { index, geometry ->
            val g = geometry
            require(g.distanceMeters.isFinite() && g.distanceMeters in 1.0..10_000_000.0)
            require(g.durationSeconds.isFinite() && g.durationSeconds in 1.0..604800.0)
            require(g.points.size in 2..100000 && g.segmentMeters.size == g.points.size - 1 &&
                g.segmentSeconds.size == g.points.size - 1)
            require(g.segmentMeters.all { it.isFinite() && it >= 0 } && g.segmentSeconds.all { it.isFinite() && it >= 0 })
            val meters = g.segmentMeters.sum(); val seconds = g.segmentSeconds.sum()
            require(meters > 0 && seconds > 0 && abs(meters - g.distanceMeters) < max(10.0, g.distanceMeters * .01))
            val geographicMeters = g.points.zipWithNext().sumOf { (a, b) -> a.distanceTo(b) }
            require(abs(geographicMeters - g.distanceMeters) < max(100.0, g.distanceMeters * .05)) { "도로 좌표와 거리 응답이 일치하지 않습니다." }
            require(g.points.last().distanceTo(destination.point) <= 1000) { "목적지와 도로 도착점이 너무 멉니다." }
            var distance = 0.0; var time = 0.0
            val nodes = mutableListOf(RouteNode(key(g.points.first()), g.points.first(), 0.0, 0.0))
            for (i in g.segmentMeters.indices) {
                distance += g.segmentMeters[i]; time += g.segmentSeconds[i]
                if (g.segmentMeters[i] <= 0) continue
                nodes.add(RouteNode(key(g.points[i + 1]), g.points[i + 1], distance / meters * g.distanceMeters / 1000,
                    time / seconds * g.durationSeconds / 60))
            }
            require(nodes.size >= 2)
            nodes[nodes.lastIndex] = nodes.last().copy(distanceKm = g.distanceMeters / 1000, elapsedMinutes = g.durationSeconds / 60)
            val type = when { index == 0 -> RouteType.FASTEST; index == shortest -> RouteType.ECO; else -> RouteType.BALANCED }
            val label = when { index == 0 -> "빠른 경로"; index == shortest -> "짧은 경로"; else -> "대안 경로 $index" }
            val energy = EnergyEngine.predict(g.distanceMeters / 1000, vehicle.efficiencyKmPerKwh)
            RouteCandidate("osrm_${destination.id}_$index", type, label, "OSRM 도로 경로", g.distanceMeters / 1000,
                g.durationSeconds / 60, energy, EnergyEngine.arrivalSoc(vehicle.socPercent, vehicle.usableBatteryCapacityKwh, energy),
                1.0, nodes, RouteSource.OSRM)
        }
    }
    private fun key(p: GeoPoint) = "osm:${p.latitude}:${p.longitude}"
}
