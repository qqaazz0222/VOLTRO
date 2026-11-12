package com.qqaazz0222.voltro.domain.model

data class JunctionAdvice(
    val id: String, val distanceMeters: Double, val alternative: RouteCandidate,
    val savingKwh: Double, val additionalMinutes: Double, val arrivalSoc: Double,
)

data class DrivingState(
    val tripId: String, val activeRoute: RouteCandidate, val initialRoute: RouteCandidate,
    val startedAt: Long = System.currentTimeMillis(), val distanceKm: Double = 0.0,
    val elapsedMinutes: Double = 0.0, val consumedKwh: Double = 0.0,
    val position: GeoPoint = activeRoute.nodes.first().point,
    val paused: Boolean = false, val speed: Int = 4,
    val advice: JunctionAdvice? = null, val junctionChecked: Boolean = false,
    val routeChanged: Boolean = false,
)

data class TripRecord(
    val id: String, val destination: String, val routeLabel: String, val startedAt: Long, val endedAt: Long,
    val distanceKm: Double, val durationMinutes: Double,
    val estimatedEnergyKwh: Double, val simulatedEnergyKwh: Double,
    val initialSoc: Double, val finalSoc: Double, val remote: Boolean = false, val synced: Boolean = false,
)
