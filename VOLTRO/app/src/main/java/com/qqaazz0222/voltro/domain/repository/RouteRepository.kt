package com.qqaazz0222.voltro.domain.repository

import com.qqaazz0222.voltro.domain.model.*

interface RouteRepository {
    suspend fun compare(destination: Destination, vehicle: VehicleEnergyState, preferences: Preferences): RouteComparison
}
