package com.qqaazz0222.voltro.data.pleos

import com.qqaazz0222.voltro.domain.model.*
import com.qqaazz0222.voltro.domain.repository.*

/** Capability gate. No guessed Pleos SDK calls; never wired as real navigation. */
class PleosNavigationRepository : NavigationRepository {
    override val canSelectRoute = false
    override suspend fun setDestination(destination: GeoPoint): Result<Unit> =
        Result.failure(UnsupportedOperationException("Pleos SDK 연동이 확인되지 않았습니다."))
    override suspend fun requestRouteChange(route: RouteCandidate) =
        RouteChangeResult.Unsupported("실차 경로 변경은 지원하지 않습니다.")
}
