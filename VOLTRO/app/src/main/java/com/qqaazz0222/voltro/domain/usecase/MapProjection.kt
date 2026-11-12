package com.qqaazz0222.voltro.domain.usecase

import com.qqaazz0222.voltro.domain.model.GeoPoint
import kotlin.math.*

object MapProjection {
    fun project(point: GeoPoint): Pair<Double, Double> {
        val lat = Math.toRadians(point.latitude.coerceIn(-85.05112878, 85.05112878))
        return (point.longitude + 180) / 360 to (1 - ln(tan(lat) + 1 / cos(lat)) / PI) / 2
    }
    fun unproject(x: Double, y: Double): GeoPoint = GeoPoint(
        Math.toDegrees(atan(sinh(PI * (1 - 2 * y.coerceIn(0.0, 1.0))))),
        x.coerceIn(0.0, 1.0) * 360 - 180)
}
