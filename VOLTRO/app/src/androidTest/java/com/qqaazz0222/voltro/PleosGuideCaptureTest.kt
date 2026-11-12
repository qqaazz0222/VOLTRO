package com.qqaazz0222.voltro

import android.graphics.Bitmap
import android.os.Build
import android.os.SystemClock
import android.view.PixelCopy
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.lifecycle.ViewModelProvider
import androidx.test.core.app.ActivityScenario
import androidx.test.espresso.Espresso.onView
import androidx.test.espresso.UiController
import androidx.test.espresso.ViewAction
import androidx.test.espresso.matcher.RootMatchers.isDialog
import androidx.test.espresso.matcher.ViewMatchers.*
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.qqaazz0222.voltro.domain.model.*
import com.qqaazz0222.voltro.presentation.*
import org.hamcrest.Matcher
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

/** Opt-in documentation capture. Native window pixels from a running Pleos app; no UI mockups. */
@RunWith(AndroidJUnit4::class)
class PleosGuideCaptureTest {
    private val instrumentation = InstrumentationRegistry.getInstrumentation()
    private val out = File(instrumentation.targetContext.filesDir, "pleos-guide").apply { mkdirs() }
    private lateinit var activity: MainActivity
    private lateinit var vm: VoltroViewModel
    private fun main(action: () -> Unit) = instrumentation.runOnMainSync(action)
    private fun await(timeout: Long = 35000, condition: () -> Boolean) {
        val until = SystemClock.elapsedRealtime() + timeout
        while (!condition() && SystemClock.elapsedRealtime() < until) SystemClock.sleep(150)
        assertTrue("Capture state timed out: ${vm.state.value.error}", condition())
        SystemClock.sleep(250)
    }
    private fun findText(root: View, text: String): View? {
        if (root is TextView && root.text.toString() == text) return root
        if (root is ViewGroup) for (i in 0 until root.childCount) findText(root.getChildAt(i), text)?.let { return it }
        return null
    }
    private fun click(text: String) = main {
        val view = findText(activity.window.decorView, text) ?: error("Control absent: $text")
        assertTrue(view.performClick())
    }
    private fun capture(name: String, fullDisplay: Boolean = false) {
        SystemClock.sleep(400)
        if (fullDisplay) {
            instrumentation.uiAutomation.takeScreenshot()!!.let { bitmap ->
                File(out, "$name.png").outputStream().use { bitmap.compress(Bitmap.CompressFormat.PNG, 100, it) }
                bitmap.recycle()
            }
        } else {
            check(Build.VERSION.SDK_INT >= 34)
            val finished = CountDownLatch(1)
            var copied: Bitmap? = null
            var status = -1
            main {
                val request = PixelCopy.Request.Builder.ofWindow(activity.window).build()
                PixelCopy.request(request, { it.run() }) { result ->
                    status = result.status
                    if (status == PixelCopy.SUCCESS) copied = result.bitmap
                    finished.countDown()
                }
            }
            assertTrue(finished.await(10, TimeUnit.SECONDS)); assertEquals(PixelCopy.SUCCESS, status)
            copied!!.let { bitmap ->
                File(out, "$name.png").outputStream().use { bitmap.compress(Bitmap.CompressFormat.PNG, 100, it) }
                bitmap.recycle()
            }
        }
        println("Captured $name")
    }

    @Test fun captureVehicleGuideFromRealRoadAndOfflineFlows() {
        assertTrue(Build.VERSION.SDK_INT >= 34)
        ActivityScenario.launch(MainActivity::class.java).use { scenario ->
            scenario.onActivity {
                activity = it
                assertTrue(it.resources.configuration.screenWidthDp >= 800)
                vm = ViewModelProvider(it)[VoltroViewModel::class.java]
                vm.configure(15.0, 15.0, 68.0, 5.2, 70.0, false, false, roadMode = true)
                vm.clearNotice()
            }
            capture("pleos-home")
            click("Pleos 차량 상태 읽기")
            await { !vm.state.value.busy }
            assertEquals("SDK snapshot required for this guide capture", DataSource.PLEOS, vm.state.value.vehicle.source)
            capture("pleos-sdk")
            main { vm.clearNotice(); vm.selectDestination(vm.destinations.first()) }
            // The same analyze button and query path used by users.
            main { activity.findViewById<View>(R.id.analyze_routes).performClick() }
            await { !vm.state.value.busy }
            assertNull(vm.state.value.error)
            assertTrue(vm.state.value.comparison!!.roadNetwork)
            // Wait for this one visible viewport; never pan/scan to prefetch tiles.
            val loaded = CountDownLatch(1)
            for (i in 0 until 60) {
                var waiting = false
                main { waiting = findText(activity.window.decorView, "지도 로딩 중…") != null }
                if (!waiting) { loaded.countDown(); break }
                SystemClock.sleep(250)
            }
            assertEquals(0L, loaded.count)
            main { assertNull(findText(activity.window.decorView, "지도 연결 실패 · 탭하여 재시도")) }
            capture("pleos-comparison"); capture("pleos-full-road", true)
            val comparison = vm.state.value.comparison!!
            val metrics = JSONObject().put("version", "1.1.0-mvp").put("soc", vm.state.value.vehicle.socPercent)
                .put("vehicle_source", vm.state.value.vehicle.source.name).put("trip_id", comparison.tripId)
                .put("routes", JSONArray(comparison.routes.map { r -> JSONObject().put("label", r.label).put("id", r.id)
                    .put("distance_km", r.distanceKm).put("minutes", r.durationMinutes)
                    .put("energy_kwh", r.energyKwh).put("arrival_soc", r.arrivalSoc).put("geometry_points", r.nodes.size) }))
            main { activity.findViewById<View>(R.id.start_trip).performClick() }
            SystemClock.sleep(2500)
            main { if (vm.state.value.driving?.paused == false) vm.togglePause() }
            capture("pleos-driving")
            main { if (vm.state.value.driving?.paused == true) vm.togglePause() }
            await(45000) {
                if (vm.state.value.driving?.advice != null) main { vm.dismissAdvice() }
                vm.state.value.screen == Screen.REPORT && !vm.state.value.busy
            }
            metrics.put("completed_route", vm.state.value.report!!.routeLabel)
                .put("completed_energy_kwh", vm.state.value.report!!.simulatedEnergyKwh)
                .put("completed_km", vm.state.value.report!!.distanceKm)
            capture("pleos-report")
            main { vm.history() }; capture("pleos-history")
            main { vm.home(); vm.configure(15.0, 15.0, 68.0, 5.2, 70.0, false, false, roadMode = true); vm.analyze("강릉역") }
            await { !vm.state.value.busy }
            assertTrue(vm.state.value.comparison!!.routes.all { it.arrivalSoc < 15.0 })
            capture("pleos-soc-blocked")
            main { vm.home() }
            click("설정"); capture("pleos-settings", true)
            // Close the real settings dialog through the standard UI action.
            onView(withText("취소")).inRoot(isDialog()).perform(object : ViewAction {
                override fun getConstraints(): Matcher<View> = isDisplayed()
                override fun getDescription() = "Close vehicle settings"
                override fun perform(uiController: UiController, view: View) { view.performClick(); uiController.loopMainThreadUntilIdle() }
            })
            main {
                vm.configure(15.0, 15.0, 68.0, 5.2, 70.0, false, false, roadMode = false)
                vm.selectDestination(vm.destinations.first()); vm.analyze("강릉역")
            }
            await { !vm.state.value.busy }
            main {
                vm.selectRoute(vm.state.value.comparison!!.routes.first { it.type == RouteType.FASTEST }.id)
                vm.startDriving()
            }
            await { vm.state.value.driving?.advice != null }
            capture("pleos-junction-demo")
            main { vm.stopDriving(); vm.setRoadMode(true) }
            File(out, "metrics.json").writeText(metrics.toString(2))
            println("Capture directory: ${out.absolutePath}")
        }
    }
}
