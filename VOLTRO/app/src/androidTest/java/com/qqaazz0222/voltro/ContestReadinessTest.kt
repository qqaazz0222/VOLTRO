package com.qqaazz0222.voltro

import android.os.SystemClock
import androidx.lifecycle.ViewModelProvider
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.qqaazz0222.voltro.data.local.*
import com.qqaazz0222.voltro.data.mock.MockRouteRepository
import com.qqaazz0222.voltro.domain.model.*
import com.qqaazz0222.voltro.presentation.*
import kotlinx.coroutines.runBlocking
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.After
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File

@RunWith(AndroidJUnit4::class)
class ContestReadinessTest {
    private val context get() = InstrumentationRegistry.getInstrumentation().targetContext
    private val sessions get() = DrivingSessionStore(context)
    @Before fun cleanCheckpoint() { sessions.clear() }
    @After fun cleanup() { sessions.clear() }
    private fun await(condition: () -> Boolean) {
        val end = SystemClock.elapsedRealtime() + 15000
        while (!condition() && SystemClock.elapsedRealtime() < end) SystemClock.sleep(50)
        assertTrue("Contest state did not settle", condition())
        InstrumentationRegistry.getInstrumentation().waitForIdleSync()
    }
    private fun capture(name: String) {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        instrumentation.waitForIdleSync()
        // StateFlow delivery and Pleos launcher transitions can finish after main-thread idleness.
        SystemClock.sleep(800)
        instrumentation.waitForIdleSync()
        val bitmap = instrumentation.uiAutomation.takeScreenshot()
        val directory = File(context.filesDir, "contest-captures").apply { mkdirs() }
        File(directory, "$name.png").outputStream().use { bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, it) }
        bitmap.recycle()
    }
    private fun seed(): DrivingSession = runBlocking {
        val repository = MockRouteRepository(JSONObject(context.assets.open("scenario.json").bufferedReader().use { it.readText() }))
        val comparison = repository.compare(repository.destinations.first(), VehicleEnergyState(), Preferences())
        val fast = comparison.routes.first { it.type == RouteType.FASTEST }
        val eco = comparison.routes.first { it.type == RouteType.ECO }
        val driving = DrivingState(comparison.tripId, fast, fast, distanceKm = 33.8, elapsedMinutes = 24.14,
            consumedKwh = 33.8 / 5.2, position = fast.pointAt(33.8), speed = 12,
            advice = JunctionAdvice("decision", 1200.0, eco, 15 / 5.2, 15.0, eco.arrivalSoc))
        DrivingSession(VehicleEnergyState(), Preferences(), comparison, driving, setOf("decision"), setOf("junction"), true)
    }

    @Test fun allThreeScenariosPrepareWithoutChangingSavedProfile() {
        val settings = context.getSharedPreferences("voltro", 0)
        val before = settings.all.toMap()
        ActivityScenario.launch(MainActivity::class.java).use { activity ->
            lateinit var vm: VoltroViewModel
            activity.onActivity { vm = ViewModelProvider(it)[VoltroViewModel::class.java]; vm.prepareDemo(DemoScenario.SAVING) }
            await { vm.state.value.screen == Screen.COMPARISON && !vm.state.value.busy }
            val selected = vm.state.value.comparison!!.routes.first { it.id == vm.state.value.selectedId }
            assertEquals(RouteType.FASTEST, selected.type)
            assertEquals(DataSource.MOCK, vm.state.value.vehicle.source)
            capture("comparison")
            activity.onActivity { vm.home(); vm.prepareDemo(DemoScenario.LOW_BATTERY) }
            await { vm.state.value.vehicle.socPercent == 20.0 && !vm.state.value.busy }
            assertNull(vm.state.value.selectedId)
            capture("low-soc")
            activity.onActivity { vm.startDriving() }
            assertNull(vm.state.value.driving)
            activity.onActivity { vm.home(); vm.prepareDemo(DemoScenario.CHANGE_FAILURE) }
            await { vm.state.value.failRouteChange && !vm.state.value.busy }
            assertEquals(RouteType.FASTEST, vm.state.value.comparison!!.routes.first { it.id == vm.state.value.selectedId }.type)
        }
        assertEquals(before, settings.all)
    }

    @Test fun replayRestoresPausedWithDecisionAndDeduplicationState() {
        val saved = seed(); sessions.save(saved)
        val decoded = sessions.read()!!
        assertEquals(saved.notified, decoded.notified)
        assertEquals(saved.processedJunctions, decoded.processedJunctions)
        assertEquals(saved.comparison, decoded.comparison)
        ActivityScenario.launch(MainActivity::class.java).use { activity ->
            lateinit var vm: VoltroViewModel
            activity.onActivity { vm = ViewModelProvider(it)[VoltroViewModel::class.java]; assertTrue(vm.state.value.recoveryAvailable); vm.restoreDriving() }
            await { vm.state.value.driving != null && !vm.state.value.busy }
            val driving = vm.state.value.driving!!
            assertTrue(driving.paused)
            assertEquals(saved.driving.tripId, driving.tripId)
            assertEquals(saved.driving.distanceKm, driving.distanceKm, 1e-9)
            assertEquals(saved.driving.consumedKwh, driving.consumedKwh, 1e-9)
            assertEquals(saved.driving.advice, driving.advice)
            capture("recovery")
            activity.onActivity { vm.togglePause() }
            SystemClock.sleep(700)
            assertTrue(vm.state.value.driving!!.paused)
            assertEquals(driving.distanceKm, vm.state.value.driving!!.distanceKm, 1e-9)
            activity.onActivity { vm.stopDriving() }
            await { !sessions.exists() }
            TripStore(context).use { assertFalse(it.recent().any { record -> record.id == driving.tripId }) }
        }
    }

    @Test fun corruptedCheckpointIsDiscardedWithoutTouchingCompletedHistory() {
        val before = TripStore(context).use { it.recent() }
        File(context.noBackupFilesDir, "replay-session.json").writeText("{broken")
        ActivityScenario.launch(MainActivity::class.java).use { activity ->
            lateinit var vm: VoltroViewModel
            activity.onActivity { vm = ViewModelProvider(it)[VoltroViewModel::class.java]; vm.restoreDriving() }
            await { !vm.state.value.busy && vm.state.value.error != null }
            assertFalse(vm.state.value.recoveryAvailable)
            assertNull(vm.state.value.driving)
            assertFalse(sessions.exists())
        }
        assertEquals(before, TripStore(context).use { it.recent() })
    }

    @Test fun completedTripWinsOverStaleCheckpointAndRemainsIdempotent() {
        val saved = seed(); sessions.save(saved)
        val record = TripRecord(saved.comparison.tripId, "강릉역", "절전", 1, 2, 165.0, 145.0,
            180 / 5.2, 165 / 5.2, 68.0, 22.67, initialDurationMinutes = 130.0, vehicleSource = "MOCK")
        TripStore(context).use { it.save(record); it.save(record) }
        ActivityScenario.launch(MainActivity::class.java).use { activity ->
            lateinit var vm: VoltroViewModel
            activity.onActivity { vm = ViewModelProvider(it)[VoltroViewModel::class.java]; vm.restoreDriving() }
            await { vm.state.value.screen == Screen.REPORT && !vm.state.value.busy }
            assertNull(vm.state.value.driving)
            assertEquals(record, vm.state.value.report)
            capture("report")
            assertFalse(sessions.exists())
        }
        TripStore(context).use { assertEquals(1, it.recent().count { record -> record.id == saved.comparison.tripId }) }
    }
}
