package com.qqaazz0222.voltro

import androidx.lifecycle.ViewModelProvider
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.espresso.Espresso.onView
import androidx.test.espresso.action.ViewActions.*
import androidx.test.espresso.assertion.ViewAssertions.matches
import androidx.test.espresso.matcher.ViewMatchers.*
import android.os.SystemClock
import com.qqaazz0222.voltro.data.local.TripStore
import com.qqaazz0222.voltro.data.local.DrivingSessionStore
import com.qqaazz0222.voltro.domain.model.RouteType
import com.qqaazz0222.voltro.presentation.*
import org.junit.Assert.*
import org.junit.Test
import org.junit.Before
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class MockJourneyTest {
    @Before fun resetOnlyReplayCheckpoint() {
        DrivingSessionStore(InstrumentationRegistry.getInstrumentation().targetContext).clear()
    }
    private fun await(timeout: Long = 30000, condition: () -> Boolean) {
        val end = SystemClock.elapsedRealtime() + timeout
        while (!condition() && SystemClock.elapsedRealtime() < end) SystemClock.sleep(50)
        assertTrue("Expected journey state before timeout", condition())
        InstrumentationRegistry.getInstrumentation().waitForIdleSync()
    }

    @Test fun fullJourneySupportsApprovedSwitchAndPersistentReport() {
        ActivityScenario.launch(MainActivity::class.java).use { scenario ->
            lateinit var vm: VoltroViewModel
            scenario.onActivity {
                vm = ViewModelProvider(it)[VoltroViewModel::class.java]
                vm.configure(15.0, 15.0, 68.0, 5.2, 70.0, false, false, roadMode = false)
                vm.selectDestination(vm.destinations.first())
            }
            onView(withId(R.id.analyze_routes)).perform(click())
            await { vm.state.value.screen == Screen.COMPARISON }
            onView(withContentDescription("빠른 경로 선택")).perform(scrollTo(), click())
            assertEquals(RouteType.FASTEST, vm.state.value.comparison!!.routes.first { it.id == vm.state.value.selectedId }.type)
            onView(withId(R.id.start_trip)).perform(click())
            scenario.onActivity { vm.changeSpeed() }
            await { vm.state.value.driving?.advice != null }
            assertTrue(vm.state.value.driving!!.paused)
            val before = vm.state.value.driving!!
            scenario.recreate()
            onView(withText("절전 경로로 변경")).perform(scrollTo(), click())
            await { vm.state.value.driving?.activeRoute?.type == RouteType.ECO }
            val after = vm.state.value.driving!!
            assertTrue(after.distanceKm >= before.distanceKm)
            assertEquals(after.activeRoute.pointAt(after.distanceKm), after.position)
            await { vm.state.value.screen == Screen.REPORT && !vm.state.value.busy && vm.state.value.history.isNotEmpty() }
            val report = vm.state.value.report!!
            assertEquals(165.0, report.distanceKm, .000001)
            assertEquals(165.0 / 5.2, report.simulatedEnergyKwh, .000001)
            assertEquals(145.0, report.durationMinutes, .000001)
            assertFalse(report.remote)
            assertFalse("Completed replay must be cleared before the next journey is enabled", DrivingSessionStore(InstrumentationRegistry.getInstrumentation().targetContext).exists())
            onView(withText("SIMULATED TRIP")).check(matches(isDisplayed()))
            TripStore(InstrumentationRegistry.getInstrumentation().targetContext).use { store ->
                assertTrue(store.recent().any { it.id == report.id })
            }
        }
    }

    @Test fun unsupportedSwitchKeepsOriginalRouteAndCancellationDoesNotCompleteTrip() {
        ActivityScenario.launch(MainActivity::class.java).use { scenario ->
            lateinit var vm: VoltroViewModel
            scenario.onActivity {
                vm = ViewModelProvider(it)[VoltroViewModel::class.java]
                vm.configure(15.0, 15.0, 68.0, 5.2, 70.0, false, true, roadMode = false)
                vm.selectDestination(vm.destinations.first()); vm.analyze("강릉역")
            }
            await { vm.state.value.screen == Screen.COMPARISON }
            scenario.onActivity { vm.selectRoute(vm.state.value.comparison!!.routes.first { it.type == RouteType.FASTEST }.id); vm.startDriving(); vm.changeSpeed() }
            await { vm.state.value.driving?.advice != null }
            scenario.onActivity { vm.acceptAdvice() }
            await { vm.state.value.error != null && !vm.state.value.busy }
            assertEquals(RouteType.FASTEST, vm.state.value.driving!!.activeRoute.type)
            assertNull(vm.state.value.driving!!.advice)
            assertTrue("Failed route change must pause for explicit continuation", vm.state.value.driving!!.paused)
            val tripId = vm.state.value.driving!!.tripId
            scenario.onActivity { vm.stopDriving() }
            await { vm.state.value.screen == Screen.HOME && !vm.state.value.busy }
            assertFalse(DrivingSessionStore(InstrumentationRegistry.getInstrumentation().targetContext).exists())
            TripStore(InstrumentationRegistry.getInstrumentation().targetContext).use { store ->
                assertFalse(store.recent().any { it.id == tripId })
            }
        }
    }

    @Test fun insufficientSocBlocksEveryRoute() {
        ActivityScenario.launch(MainActivity::class.java).use { scenario ->
            lateinit var vm: VoltroViewModel
            scenario.onActivity {
                vm = ViewModelProvider(it)[VoltroViewModel::class.java]
                vm.configure(15.0, 15.0, 20.0, 5.2, 70.0, false, false, roadMode = false)
                vm.selectDestination(vm.destinations.first()); vm.analyze("강릉역")
            }
            await { vm.state.value.screen == Screen.COMPARISON }
            assertNull(vm.state.value.comparison!!.recommendedId)
            assertNull(vm.state.value.selectedId)
            onView(withId(R.id.start_trip)).check(matches(isNotEnabled()))
            scenario.onActivity { vm.configure(15.0, 15.0, 68.0, 5.2, 70.0, false, false, roadMode = false) }
            assertEquals(Screen.HOME, vm.state.value.screen)
            assertNull(vm.state.value.comparison)
        }
    }
}
