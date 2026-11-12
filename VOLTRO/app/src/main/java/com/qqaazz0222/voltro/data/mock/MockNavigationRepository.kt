package com.qqaazz0222.voltro.data.mock

import com.qqaazz0222.voltro.domain.model.*
import com.qqaazz0222.voltro.domain.repository.*

class MockNavigationRepository : NavigationRepository {
    override val canSelectRoute = true
    var simulateChangeFailure = false
    override suspend fun setDestination(destination: GeoPoint) = Result.success(Unit)
    override suspend fun requestRouteChange(route: RouteCandidate): RouteChangeResult =
        if (simulateChangeFailure) RouteChangeResult.Unsupported("Mock 경로 변경 실패 · 기존 경로를 유지합니다.")
        else RouteChangeResult.Changed
}
