package com.qqaazz0222.voltro.presentation

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.qqaazz0222.voltro.data.local.TripStore
import com.qqaazz0222.voltro.data.mock.*
import com.qqaazz0222.voltro.data.remote.*
import com.qqaazz0222.voltro.data.pleos.PleosVehicleRepository
import com.qqaazz0222.voltro.domain.model.*
import com.qqaazz0222.voltro.domain.repository.RouteChangeResult
import com.qqaazz0222.voltro.domain.usecase.*
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import org.json.JSONObject
import kotlin.math.*

enum class Screen { HOME, COMPARISON, DRIVING, REPORT, HISTORY }
data class AppState(
    val screen: Screen = Screen.HOME, val vehicle: VehicleEnergyState = VehicleEnergyState(),
    val preferences: Preferences = Preferences(), val serverMode: Boolean = false,
    val busy: Boolean = false, val error: String? = null, val message: String? = null,
    val destination: Destination? = null, val comparison: RouteComparison? = null,
    val selectedId: String? = null, val driving: DrivingState? = null,
    val report: TripRecord? = null, val history: List<TripRecord> = emptyList(),
    val failRouteChange: Boolean = false,
)

class VoltroViewModel(application: Application) : AndroidViewModel(application) {
    private val developerBuild = application.applicationInfo.flags and android.content.pm.ApplicationInfo.FLAG_DEBUGGABLE != 0
    private val settings = application.getSharedPreferences("voltro", 0)
    private fun storedNumber(key: String, fallback: Double) = settings.all[key]?.toString()?.toDoubleOrNull() ?: fallback
    private val local = MockRouteRepository(JSONObject(application.assets.open("scenario.json").bufferedReader().use { it.readText() }))
    private val client = BackendClient()
    private val remote = RemoteRouteRepository(client, local.origin)
    private val navigation = MockNavigationRepository()
    private val store = TripStore(application)
    private val mutable = MutableStateFlow(AppState(
        vehicle = VehicleEnergyState(storedNumber("soc", 68.0), storedNumber("efficiency", 5.2),
            storedNumber("capacity", 70.0), source = if (settings.getBoolean("manualVehicle", false)) DataSource.USER_INPUT else DataSource.MOCK),
        preferences = Preferences(storedNumber("minSoc", 15.0), storedNumber("extra", 15.0)),
        serverMode = developerBuild && settings.getBoolean("server", false),
    ))
    val state = mutable.asStateFlow()
    val destinations = local.destinations
    val origin = local.origin
    private var ticker: Job? = null
    private val notified = mutableSetOf<String>()
    private var lastQuery = ""
    private val exceptionHandler = CoroutineExceptionHandler { _, throwable ->
        mutable.update { it.copy(busy = false, error = "처리하지 못했습니다. ${throwable.message.orEmpty()}") }
    }

    init { refreshHistory() }
    private fun refreshHistory() = viewModelScope.launch(exceptionHandler) {
        val records = withContext(Dispatchers.IO) { store.recent() }
        mutable.update { it.copy(history = records) }
    }

    fun selectDestination(destination: Destination) {
        mutable.update { it.copy(destination = destination, error = null) }
    }
    fun readPleosVehicle() {
        if (state.value.busy || state.value.driving != null) return
        mutable.update { it.copy(busy = true, error = null, message = "Pleos 차량 상태를 확인하고 있습니다…") }
        viewModelScope.launch(exceptionHandler) {
            try {
                val snapshot = PleosVehicleRepository(getApplication(), state.value.vehicle).getVehicleEnergyState()
                mutable.update { it.copy(vehicle = snapshot, comparison = null, selectedId = null, busy = false,
                    message = "Pleos SOC를 불러왔습니다. 용량은 설정값이며 경로·주행은 데모입니다.") }
            } catch (cancelled: CancellationException) {
                if (cancelled is TimeoutCancellationException) mutable.update { it.copy(busy = false, message = null,
                    error = "Pleos 응답 시간이 초과되었습니다. 기존 차량값을 유지합니다.") }
                else throw cancelled
            } catch (_: Exception) {
                mutable.update { it.copy(busy = false, message = null,
                    error = "Pleos 차량값을 읽지 못했습니다. SDK 서비스·권한·지원 여부를 확인하세요. 기존 차량값을 유지합니다.") }
            }
        }
    }
    fun clearNotice() { mutable.update { it.copy(error = null, message = null) } }
    fun serverPermissionDenied() {
        mutable.update { it.copy(error = "개발 서버 연결에는 로컬 네트워크 권한이 필요합니다. 오프라인 데모도 사용할 수 있습니다.") }
    }
    fun analyze(query: String) {
        if (state.value.busy || state.value.driving != null) return
        lastQuery = query
        val destination = destinations.firstOrNull { query.isNotBlank() && (it.name.contains(query.trim(), true) || query.contains(it.name, true)) }
            ?: state.value.destination.takeIf { query.isBlank() || query == it?.name }
        if (destination == null) {
            mutable.update { it.copy(error = "데모 목적지인 강릉역, 속초해수욕장, 양양 서피비치 중 선택하세요.") }
            return
        }
        mutable.update { it.copy(busy = true, error = null, message = null) }
        viewModelScope.launch(exceptionHandler) {
            val snapshot = state.value
            try {
                val result = (if (snapshot.serverMode) remote else local).compare(destination, snapshot.vehicle, snapshot.preferences)
                mutable.update { it.copy(busy = false, destination = destination, comparison = result,
                    selectedId = result.recommendedId ?: result.routes.firstOrNull { r -> r.arrivalSoc >= snapshot.preferences.minArrivalSoc }?.id,
                    screen = Screen.COMPARISON) }
            } catch (cancelled: CancellationException) { throw cancelled }
            catch (_: Exception) {
                mutable.update { it.copy(busy = false, error = "서버에 연결하지 못했거나 경로 응답이 유효하지 않습니다. 기존 분석을 유지했습니다. 서버를 확인한 뒤 다시 시도하세요.") }
            }
        }
    }
    fun retryAnalysis() = analyze(lastQuery)
    fun selectRoute(id: String) {
        if (state.value.driving != null || state.value.busy) return
        val route = state.value.comparison?.routes?.firstOrNull { it.id == id } ?: return
        if (route.arrivalSoc < state.value.preferences.minArrivalSoc) return
        mutable.update { it.copy(selectedId = id, error = null) }
    }
    fun configure(minSoc: Double, maxExtra: Double, soc: Double, efficiency: Double, capacity: Double,
                  server: Boolean, failChange: Boolean) {
        if (state.value.driving != null || state.value.busy) return
        require(!server || developerBuild) { "개발 서버는 debug 빌드에서만 사용할 수 있습니다." }
        val preferences = Preferences(minSoc, maxExtra)
        val source = if (soc == 68.0 && efficiency == 5.2 && capacity == 70.0) DataSource.MOCK else DataSource.USER_INPUT
        val vehicle = VehicleEnergyState(soc, efficiency, capacity, source = source)
        settings.edit().putString("minSoc", minSoc.toString()).putString("extra", maxExtra.toString())
            .putBoolean("server", server).putString("soc", soc.toString()).putString("efficiency", efficiency.toString())
            .putString("capacity", capacity.toString()).putBoolean("manualVehicle", source == DataSource.USER_INPUT).apply()
        navigation.simulateChangeFailure = failChange
        mutable.update { it.copy(screen = Screen.HOME, preferences = preferences, vehicle = vehicle, serverMode = server,
            comparison = null, selectedId = null, failRouteChange = failChange, error = null, message = "설정을 적용했습니다.") }
    }
    fun checkServer() {
        if (state.value.busy || state.value.driving != null) return
        mutable.update { it.copy(busy = true, error = null, message = null) }
        viewModelScope.launch(exceptionHandler) {
            try {
                val health = client.request("/health")
                require(health.getString("status") == "ok" && health.getString("mode") == "mock")
                val vehicle = client.request("/api/v1/vehicle")
                require(vehicle.getDouble("soc_percent") in 0.0..100.0)
                mutable.update { it.copy(busy = false, message = "서버 연결 정상 · Mock 차량 API 확인 완료") }
            } catch (cancelled: CancellationException) { throw cancelled }
            catch (_: Exception) { mutable.update { it.copy(busy = false, error = "서버 연결 실패 · 10.0.2.2:8000의 개발 서버를 확인하세요.") } }
        }
    }
    fun home() {
        if (state.value.driving != null || state.value.busy) return
        mutable.update { it.copy(screen = Screen.HOME, error = null, message = null) }
    }
    fun history() {
        if (state.value.driving != null || state.value.busy) return
        mutable.update { it.copy(screen = Screen.HISTORY, error = null, message = null) }
        refreshHistory()
    }
    fun previousComparison() {
        if (state.value.driving == null && !state.value.busy && state.value.comparison != null)
            mutable.update { it.copy(screen = Screen.COMPARISON) }
    }
    fun openReport(record: TripRecord) { mutable.update { it.copy(screen = Screen.REPORT, report = record, error = null) } }
    fun deleteHistory() = viewModelScope.launch(exceptionHandler) {
        if (state.value.driving != null) return@launch
        withContext(Dispatchers.IO) { store.clear() }
        mutable.update { it.copy(history = emptyList(), report = null) }
    }

    fun startDriving() {
        val state = state.value
        if (state.busy || state.driving != null) return
        val comparison = state.comparison ?: return
        val route = comparison.routes.firstOrNull { it.id == state.selectedId } ?: return
        if (route.arrivalSoc < state.preferences.minArrivalSoc) return
        notified.clear()
        mutable.update { it.copy(screen = Screen.DRIVING, error = null, message = null,
            driving = DrivingState(comparison.tripId, route, route)) }
        ticker?.cancel()
        ticker = viewModelScope.launch(exceptionHandler) {
            while (isActive && this@VoltroViewModel.state.value.driving != null) {
                delay(500)
                tick()
            }
        }
    }

    private suspend fun tick() {
        val snapshot = state.value
        val driving = snapshot.driving ?: return
        if (driving.paused || snapshot.busy) return
        val route = driving.activeRoute
        val step = route.distanceKm / 120 * driving.speed * .5
        var distance = min(route.distanceKm, driving.distanceKm + step)
        val junction = snapshot.comparison?.routes?.filter { it.id != route.id }
            ?.mapNotNull { JunctionAnalyzer.divergence(route, it) }?.firstOrNull()
        // Stop exactly in the approach window even at 12×; do not skip a decision frame.
        if (!driving.junctionChecked && junction != null && driving.distanceKm < junction.node.distanceKm - 1.2 &&
            distance >= junction.node.distanceKm - 1.2) distance = junction.node.distanceKm - 1.2
        val energy = EnergyEngine.predict(distance - driving.distanceKm, snapshot.vehicle.efficiencyKmPerKwh)
        val next = driving.copy(distanceKm = distance, consumedKwh = driving.consumedKwh + energy,
            elapsedMinutes = driving.elapsedMinutes + route.minutesAt(distance) - route.minutesAt(driving.distanceKm),
            position = route.pointAt(distance), advice = if (junction != null && distance >= junction.node.distanceKm) null else driving.advice)
        mutable.update { it.copy(driving = next) }
        if (distance >= route.distanceKm) { finishTrip(); return }
        if (!next.junctionChecked && junction != null && distance >= junction.node.distanceKm - 1.5) evaluateJunction(next)
    }

    private suspend fun evaluateJunction(driving: DrivingState) {
        val snapshot = state.value
        val comparison = snapshot.comparison ?: return
        val soc = EnergyEngine.arrivalSoc(snapshot.vehicle.socPercent, snapshot.vehicle.usableBatteryCapacityKwh, driving.consumedKwh).coerceIn(0.0, 100.0)
        var advice: JunctionAdvice? = null
        var failure: String? = null
        try {
            if (comparison.remote) {
                val response = client.request("/api/v1/junctions/evaluate", JSONObject()
                    .put("trip_id", driving.tripId).put("active_route_id", driving.activeRoute.id)
                    .put("location", driving.position.json()).put("current_soc_percent", soc)
                    .put("accuracy_meters", 5).put("navigation_selectable", navigation.canSelectRoute))
                if (response.optBoolean("should_notify")) {
                    val alternative = comparison.routes.first { it.id == response.getString("alternative_route_id") }
                    // Recheck the server's advice against local location/capability/policy before presenting it.
                    advice = JunctionAnalyzer.evaluate(driving.activeRoute, alternative, driving.position, 5.0,
                        snapshot.vehicle, soc, snapshot.preferences, navigation.canSelectRoute)
                }
            } else {
                advice = comparison.routes.filter { it.id != driving.activeRoute.id }.mapNotNull {
                    JunctionAnalyzer.evaluate(driving.activeRoute, it, driving.position, 5.0, snapshot.vehicle,
                        soc, snapshot.preferences, navigation.canSelectRoute)
                }.maxByOrNull { it.savingKwh }
            }
        } catch (cancelled: CancellationException) { throw cancelled }
        catch (_: Exception) { failure = "분기점 분석에 실패했습니다. 기존 경로를 유지합니다." }
        val key = "${driving.activeRoute.id}:${advice?.id}"
        if (!notified.add(key)) advice = null
        val displayed = advice
        mutable.update { it.copy(error = failure, driving = it.driving?.copy(
            junctionChecked = true, advice = displayed, paused = displayed != null)) }
    }

    fun togglePause() {
        mutable.update { it.copy(driving = it.driving?.let { d ->
            d.copy(paused = !d.paused, advice = if (d.paused) null else d.advice) }) }
    }
    fun changeSpeed() { mutable.update { it.copy(driving = it.driving?.let { d -> d.copy(speed = when (d.speed) { 1 -> 4; 4 -> 12; else -> 1 }) }) } }
    fun dismissAdvice() { mutable.update { it.copy(driving = it.driving?.copy(advice = null, paused = false)) } }
    fun acceptAdvice() {
        val advice = state.value.driving?.advice ?: return
        if (state.value.busy) return
        mutable.update { it.copy(busy = true, error = null) }
        viewModelScope.launch(exceptionHandler) {
            when (val result = navigation.requestRouteChange(advice.alternative)) {
                RouteChangeResult.Changed -> mutable.update { it.copy(busy = false, message = "Mock 경로를 변경했습니다.",
                    driving = it.driving?.copy(activeRoute = advice.alternative, advice = null, paused = false,
                        routeChanged = true, junctionChecked = false)) }
                is RouteChangeResult.Unsupported -> mutable.update { it.copy(busy = false, error = result.reason,
                    driving = it.driving?.copy(advice = null, paused = false)) }
            }
        }
    }
    fun stopDriving() {
        ticker?.cancel()
        mutable.update { it.copy(driving = null, screen = Screen.HOME, busy = false,
            message = "데모 주행을 취소했습니다. 완료 이력으로 저장하지 않습니다.", error = null) }
    }
    fun pauseForBackground() {
        mutable.update { it.copy(driving = it.driving?.copy(paused = true)) }
    }

    private suspend fun finishTrip() {
        val snapshot = state.value
        val driving = snapshot.driving ?: return
        val comparison = snapshot.comparison ?: return
        val finalSoc = EnergyEngine.arrivalSoc(snapshot.vehicle.socPercent, snapshot.vehicle.usableBatteryCapacityKwh, driving.consumedKwh)
        val report = TripRecord(driving.tripId, comparison.destination.name, driving.activeRoute.label,
            driving.startedAt, System.currentTimeMillis(), driving.distanceKm, driving.elapsedMinutes,
            driving.initialRoute.energyKwh, driving.consumedKwh, snapshot.vehicle.socPercent, finalSoc,
            remote = comparison.remote)
        mutable.update { it.copy(busy = true, driving = null, screen = Screen.REPORT, report = report, error = null, message = null) }
        try {
            withContext(Dispatchers.IO) { store.save(report) }
        } catch (cancelled: CancellationException) { throw cancelled }
        catch (_: Exception) { mutable.update { it.copy(busy = false, error = "주행은 완료했지만 기기 저장에 실패했습니다. 리포트 저장을 다시 시도하세요.") }; return }
        mutable.update { it.copy(busy = false) }
        refreshHistory()
        if (report.remote) syncReport()
    }
    fun syncReport() {
        val report = state.value.report ?: return
        if (state.value.busy) return
        mutable.update { it.copy(busy = true, error = null) }
        viewModelScope.launch(exceptionHandler) {
            try {
                withContext(Dispatchers.IO) { store.save(report) }
                if (report.remote) {
                    val response = client.request("/api/v1/trips/complete", JSONObject()
                        .put("trip_id", report.id).put("estimated_energy_kwh", report.estimatedEnergyKwh)
                        .put("actual_energy_kwh", JSONObject.NULL).put("simulated_energy_kwh", report.simulatedEnergyKwh)
                        .put("distance_km", report.distanceKm).put("duration_minutes", report.durationMinutes)
                        .put("energy_source", "MOCK_SOC_ESTIMATE"))
                    require(response.getString("status") == "COMPLETED")
                    val saved = report.copy(synced = true)
                    withContext(Dispatchers.IO) { store.save(saved) }
                    mutable.update { it.copy(report = saved) }
                }
                mutable.update { it.copy(busy = false, message = "리포트를 저장했습니다.") }
                refreshHistory()
            } catch (cancelled: CancellationException) { throw cancelled }
            catch (_: Exception) { mutable.update { it.copy(busy = false, error = "리포트 전송 또는 저장에 실패했습니다. 화면의 리포트를 유지했습니다. 다시 저장할 수 있습니다.") } }
        }
    }
    override fun onCleared() { ticker?.cancel(); store.close(); super.onCleared() }
}
