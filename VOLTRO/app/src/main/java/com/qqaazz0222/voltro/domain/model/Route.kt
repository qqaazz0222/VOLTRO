package com.qqaazz0222.voltro.domain.model

import kotlin.math.*

data class GeoPoint(val latitude: Double, val longitude: Double) {
    init {
        require(latitude.isFinite() && latitude in -90.0..90.0)
        require(longitude.isFinite() && longitude in -180.0..180.0)
    }
    fun distanceTo(other: GeoPoint): Double {
        val a = Math.toRadians(latitude)
        val b = Math.toRadians(other.latitude)
        val h = sin((b - a) / 2).pow(2) + cos(a) * cos(b) *
            sin(Math.toRadians(other.longitude - longitude) / 2).pow(2)
        return 6371000 * 2 * asin(sqrt(h).coerceIn(0.0, 1.0))
    }
}

data class RouteNode(val id: String, val point: GeoPoint, val distanceKm: Double)
enum class RouteType { FASTEST, BALANCED, ECO }
data class Destination(val id: String, val name: String, val description: String, val point: GeoPoint)
data class Preferences(val minArrivalSoc: Double = 15.0, val maxExtraMinutes: Double = 15.0, val minSavingKwh: Double = 1.0) {
    init {
        require(minArrivalSoc.isFinite() && minArrivalSoc in 0.0..100.0)
        require(maxExtraMinutes.isFinite() && maxExtraMinutes in 0.0..120.0)
        require(minSavingKwh.isFinite() && minSavingKwh >= 0)
    }
}
data class RouteCandidate(
    val id: String, val type: RouteType, val label: String, val roadName: String,
    val distanceKm: Double, val durationMinutes: Double,
    val energyKwh: Double, val arrivalSoc: Double, val confidence: Double,
    val nodes: List<RouteNode>,
) {
    init {
        require(distanceKm.isFinite() && distanceKm > 0)
        require(durationMinutes.isFinite() && durationMinutes > 0)
        require(energyKwh.isFinite() && energyKwh >= 0 && arrivalSoc.isFinite())
        require(confidence.isFinite() && confidence in 0.0..1.0)
        require(nodes.size >= 2 && nodes.first().distanceKm == 0.0)
        require(nodes.zipWithNext().all { (a, b) -> b.distanceKm > a.distanceKm })
        require(abs(nodes.last().distanceKm - distanceKm) < 0.001)
    }
    fun pointAt(distance: Double): GeoPoint {
        val km = distance.coerceIn(0.0, distanceKm)
        val (a, b) = nodes.zipWithNext().firstOrNull { (_, b) -> km <= b.distanceKm }
            ?: return nodes.last().point
        val t = (km - a.distanceKm) / (b.distanceKm - a.distanceKm)
        return GeoPoint(a.point.latitude + (b.point.latitude - a.point.latitude) * t,
            a.point.longitude + (b.point.longitude - a.point.longitude) * t)
    }
}

data class RouteComparison(
    val tripId: String, val destination: Destination, val routes: List<RouteCandidate>,
    val recommendedId: String?, val provider: String, val calculatedAt: String,
    val remote: Boolean = false,
)
