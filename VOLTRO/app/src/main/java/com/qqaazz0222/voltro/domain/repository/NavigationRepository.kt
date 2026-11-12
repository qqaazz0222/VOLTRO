package com.qqaazz0222.voltro.domain.repository

import com.qqaazz0222.voltro.domain.model.*

sealed interface RouteChangeResult {
    data object Changed : RouteChangeResult
    data class Unsupported(val reason: String) : RouteChangeResult
}

interface NavigationRepository {
    val canSelectRoute: Boolean
    suspend fun setDestination(destination: GeoPoint): Result<Unit>
    suspend fun requestRouteChange(route: RouteCandidate): RouteChangeResult
}
