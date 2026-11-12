package com.qqaazz0222.voltro.domain.usecase

import com.qqaazz0222.voltro.domain.model.*

object RouteRecommendation {
    fun recommend(routes: List<RouteCandidate>, preferences: Preferences): String? {
        val fastest = routes.minWithOrNull(compareBy({ it.durationMinutes }, { it.energyKwh }, { it.id })) ?: return null
        val safe = routes.filter { it.arrivalSoc >= preferences.minArrivalSoc && it.confidence >= 0.8 &&
            it.durationMinutes - fastest.durationMinutes <= preferences.maxExtraMinutes + 1e-9 }
        val eco = safe.minWithOrNull(compareBy({ it.energyKwh }, { it.durationMinutes }, { it.id })) ?: return null
        return if (fastest.energyKwh - eco.energyKwh >= preferences.minSavingKwh) eco.id
            else fastest.id.takeIf { fastest in safe }
    }
}
