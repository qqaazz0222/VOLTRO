package com.qqaazz0222.voltro.data.pleos

import android.content.Context
import ai.pleos.playground.vehicle.Vehicle
import ai.pleos.playground.vehicle.api.model.capability.AccessType
import ai.pleos.playground.vehicle.api.model.capability.CapabilityConfig
import com.qqaazz0222.voltro.domain.model.*
import com.qqaazz0222.voltro.domain.repository.VehicleDataRepository
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

/** One-shot read only snapshot. Does not collect location, control the car, or invent a usable capacity. */
class PleosVehicleRepository(private val context: Context, private val profile: VehicleEnergyState) : VehicleDataRepository {
    private val state = MutableStateFlow(profile)
    override fun observeVehicleEnergyState() = state.asStateFlow()

    override suspend fun getVehicleEnergyState(): VehicleEnergyState = withContext(Dispatchers.Main.immediate) {
        val vehicle = Vehicle(context.applicationContext)
        try {
            vehicle.initialize()
            withTimeout(6000) {
                val battery = vehicle.getEvBattery()
                val capability = request<CapabilityConfig> { complete, failed ->
                    battery.checkEvBatteryStateOfChargeCapabilities({ complete(it) }, failed)
                }
                check(capability.accessType in setOf(AccessType.READ, AccessType.READ_WRITE)) { "SOC 읽기 미지원" }
                val soc = request<Int> { complete, failed -> battery.getEvBatteryStateOfCharge(complete, failed) }
                require(soc in 0..100) { "유효하지 않은 SOC" }
                // Optional cumulative efficiency. A missing value remains an explicitly labelled profile value.
                val efficiency = try {
                    withTimeoutOrNull(1500) {
                        val config = request<CapabilityConfig> { complete, failed ->
                            battery.checkCumulativeEvEfficiencyCapabilities({ complete(it) }, failed)
                        }
                        if (config.accessType !in setOf(AccessType.READ, AccessType.READ_WRITE)) null
                        else request<Float> { complete, failed -> battery.getCumulativeEvEfficiency(complete, failed) }
                            .toDouble().takeIf { it.isFinite() && it > 0 && it <= 30 }
                    }
                } catch (cancelled: CancellationException) { throw cancelled }
                  catch (_: Exception) { null }
                profile.copy(socPercent = soc.toDouble(), efficiencyKmPerKwh = efficiency ?: profile.efficiencyKmPerKwh,
                    timestamp = System.currentTimeMillis(), source = DataSource.PLEOS,
                    efficiencySource = if (efficiency != null) DataSource.PLEOS
                        else if (profile.efficiencySource == DataSource.PLEOS) DataSource.USER_INPUT else profile.efficiencySource,
                    capacitySource = profile.capacitySource).also { state.value = it }
            }
        } finally { vehicle.release() }
    }

    private suspend fun <T : Any> request(start: ((T?) -> Unit, (Exception) -> Unit) -> Unit): T =
        suspendCancellableCoroutine { continuation ->
            start({ value ->
                if (continuation.isActive) {
                    if (value == null) continuation.resumeWithException(IllegalStateException("SDK 값 없음"))
                    else continuation.resume(value)
                }
            }, { failure -> if (continuation.isActive) continuation.resumeWithException(failure) })
        }
}
