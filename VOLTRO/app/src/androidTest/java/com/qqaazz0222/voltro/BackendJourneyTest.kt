package com.qqaazz0222.voltro

import android.os.SystemClock
import androidx.lifecycle.ViewModelProvider
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.qqaazz0222.voltro.presentation.*
import com.qqaazz0222.voltro.domain.model.RouteType
import com.qqaazz0222.voltro.data.remote.*
import com.qqaazz0222.voltro.domain.model.*
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

/** Explicit integration suite: requires the documented FastAPI development server on host port 8000. */
@RunWith(AndroidJUnit4::class)
class BackendJourneyTest {
    private fun await(condition: () -> Boolean) {
        val end = SystemClock.elapsedRealtime() + 30000
        while (!condition() && SystemClock.elapsedRealtime() < end) SystemClock.sleep(50)
        assertTrue("Backend journey state timed out", condition())
    }

    @Test fun serverComparisonJunctionAndReportWorkTogether() {
        runBlocking {
            val api = BackendClient()
            assertEquals("ok", api.request("/health").getString("status"))
            RemoteRouteRepository(api, GeoPoint(37.5665, 126.978)).compare(
                Destination("gangneung", "강릉역", "", GeoPoint(37.7644, 128.8995)), VehicleEnergyState(), Preferences())
        }
        ActivityScenario.launch(MainActivity::class.java).use { scenario ->
            lateinit var vm: VoltroViewModel
            scenario.onActivity {
                vm = ViewModelProvider(it)[VoltroViewModel::class.java]
                vm.configure(15.0, 15.0, 68.0, 5.2, 70.0, true, false)
                vm.selectDestination(vm.destinations.first()); vm.analyze("강릉역")
            }
            await { !vm.state.value.busy }
            assertNull(vm.state.value.error)
            assertTrue(vm.state.value.comparison!!.remote)
            scenario.onActivity {
                vm.selectRoute(vm.state.value.comparison!!.routes.first { it.type == RouteType.FASTEST }.id)
                vm.startDriving(); vm.changeSpeed()
            }
            await { vm.state.value.driving?.advice != null || vm.state.value.error != null }
            assertNull(vm.state.value.error)
            assertEquals(15.0 / 5.2, vm.state.value.driving!!.advice!!.savingKwh, .000001)
            scenario.onActivity { vm.acceptAdvice() }
            await { vm.state.value.report?.synced == true || vm.state.value.error != null }
            assertNull(vm.state.value.error)
            assertEquals(165.0 / 5.2, vm.state.value.report!!.simulatedEnergyKwh, .000001)
            assertTrue(vm.state.value.report!!.synced)
            scenario.onActivity { vm.home(); vm.configure(15.0, 15.0, 68.0, 5.2, 70.0, false, false) }
        }
    }
}
