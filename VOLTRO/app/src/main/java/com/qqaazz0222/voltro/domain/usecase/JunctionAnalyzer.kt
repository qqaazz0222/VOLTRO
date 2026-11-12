package com.qqaazz0222.voltro.domain.usecase

import com.qqaazz0222.voltro.domain.model.*
import kotlin.math.*

data class Junction(val node: RouteNode, val alternativeNode: RouteNode)

object JunctionAnalyzer {
    /** Only the last node of the shared prefix is a divergence; later merges are excluded. */
    fun divergence(current: RouteCandidate, alternative: RouteCandidate): Junction? {
        var count = 0
        while (count < min(current.nodes.size, alternative.nodes.size) &&
            current.nodes[count].id == alternative.nodes[count].id &&
            current.nodes[count].point.distanceTo(alternative.nodes[count].point) < 1) count++
        if (count == 0 || count == current.nodes.size || count == alternative.nodes.size) return null
        return Junction(current.nodes[count - 1], alternative.nodes[count - 1])
    }

    fun evaluate(current: RouteCandidate, alternative: RouteCandidate, position: GeoPoint,
                 accuracyMeters: Double, vehicle: VehicleEnergyState, currentSoc: Double,
                 preferences: Preferences, navigationSelectable: Boolean): JunctionAdvice? {
        if (!navigationSelectable || !accuracyMeters.isFinite() || accuracyMeters !in 0.0..50.0 ||
            !currentSoc.isFinite() || currentSoc !in 0.0..100.0) return null
        val junction = divergence(current, alternative) ?: return null
        val (along, offset) = match(current, position)
        val remaining = (junction.node.distanceKm - along) * 1000
        if (offset > 75 || remaining !in 1.0..1500.0 || min(current.confidence, alternative.confidence) < 0.8) return null
        val currentEnergy = EnergyEngine.predict(current.distanceKm - junction.node.distanceKm, vehicle.efficiencyKmPerKwh)
        val alternativeEnergy = EnergyEngine.predict(alternative.distanceKm - junction.alternativeNode.distanceKm, vehicle.efficiencyKmPerKwh)
        val saving = currentEnergy - alternativeEnergy
        val extra = (alternative.durationMinutes - alternative.minutesAt(junction.alternativeNode.distanceKm)) -
            (current.durationMinutes - current.minutesAt(junction.node.distanceKm))
        val arrival = EnergyEngine.arrivalSoc(currentSoc, vehicle.usableBatteryCapacityKwh,
            EnergyEngine.predict(alternative.distanceKm - junction.alternativeNode.distanceKm + remaining / 1000, vehicle.efficiencyKmPerKwh))
        if (saving < preferences.minSavingKwh || saving <= 0 || extra > preferences.maxExtraMinutes + 1e-9 ||
            arrival < preferences.minArrivalSoc) return null
        return JunctionAdvice(junction.node.id, remaining, alternative, saving, extra, arrival)
    }

    fun match(route: RouteCandidate, point: GeoPoint): Pair<Double, Double> {
        val scaleX = 111320 * cos(Math.toRadians(point.latitude))
        val scaleY = 111320.0
        return route.nodes.zipWithNext().map { (a, b) ->
            val ax = (a.point.longitude - point.longitude) * scaleX
            val ay = (a.point.latitude - point.latitude) * scaleY
            val dx = (b.point.longitude - a.point.longitude) * scaleX
            val dy = (b.point.latitude - a.point.latitude) * scaleY
            val length = dx * dx + dy * dy
            val t = if (length == 0.0) 0.0 else (-(ax * dx + ay * dy) / length).coerceIn(0.0, 1.0)
            (a.distanceKm + (b.distanceKm - a.distanceKm) * t) to hypot(ax + t * dx, ay + t * dy)
        }.minBy { it.second }
    }
}

/** Shared synthetic prefix takes 25 minutes for every route; suffix times remain comparable. */
fun RouteCandidate.minutesAt(distance: Double): Double {
    if (source == RouteSource.OSRM) {
        val km = distance.coerceIn(0.0, distanceKm)
        val index = nodes.binarySearch { it.distanceKm.compareTo(km) }
        if (index >= 0) return nodes[index].elapsedMinutes!!
        val next = (-index - 1).coerceIn(1, nodes.lastIndex)
        val a = nodes[next - 1]; val b = nodes[next]
        return a.elapsedMinutes!! + (b.elapsedMinutes!! - a.elapsedMinutes) * (km - a.distanceKm) / (b.distanceKm - a.distanceKm)
    }
    val split = nodes.getOrNull(2)?.distanceKm ?: return durationMinutes * distance / distanceKm
    val prefixMinutes = min(25.0, durationMinutes / 2)
    return if (distance <= split) prefixMinutes * distance / split
        else prefixMinutes + (durationMinutes - prefixMinutes) * (distance - split) / (distanceKm - split)
}
