package com.qqaazz0222.voltro

import android.os.SystemClock
import androidx.lifecycle.ViewModelProvider
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.qqaazz0222.voltro.presentation.*
import com.qqaazz0222.voltro.domain.model.RouteSource
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

/** Explicit, low-volume public-service integration check; excluded from the offline suite. */
@RunWith(AndroidJUnit4::class)
class RoadJourneyTest {
    @Test fun publicRoadGeometryLoadsAndReplaysOnAnActualMap() {
        ActivityScenario.launch(MainActivity::class.java).use { scenario ->
            lateinit var vm: VoltroViewModel
            scenario.onActivity {
                vm = ViewModelProvider(it)[VoltroViewModel::class.java]
                vm.configure(15.0, 15.0, 100.0, 5.2, 70.0, false, false, roadMode = true)
                vm.selectDestination(vm.destinations.first())
                vm.analyze("강릉역")
            }
            val deadline = SystemClock.elapsedRealtime() + 45000
            while (vm.state.value.busy && SystemClock.elapsedRealtime() < deadline) SystemClock.sleep(200)
            assertFalse("Road query timed out", vm.state.value.busy)
            assertNull(vm.state.value.error)
            val comparison = vm.state.value.comparison!!
            assertTrue(comparison.roadNetwork)
            assertTrue(comparison.routes.size in 1..3)
            assertTrue(comparison.routes.all { it.source == RouteSource.OSRM && it.nodes.size > 100 })
            assertEquals(comparison.routes.first().distanceKm / 5.2, comparison.routes.first().energyKwh, .000001)
            SystemClock.sleep(5000) // Let only this visible viewport finish rendering; no map scanning.
            InstrumentationRegistry.getInstrumentation().waitForIdleSync()
            scenario.onActivity { vm.startDriving(); vm.togglePause() }
            assertEquals(Screen.DRIVING, vm.state.value.screen)
            assertTrue(vm.state.value.driving!!.paused)
            scenario.onActivity { vm.stopDriving() }
        }
    }
}
