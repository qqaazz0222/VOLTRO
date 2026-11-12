package com.qqaazz0222.voltro

import android.os.SystemClock
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.lifecycle.ViewModelProvider
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.qqaazz0222.voltro.presentation.VoltroViewModel
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class WideLayoutTest {
    @Test fun vehicleTextIsReadableAndHeaderActionsDoNotWrap() {
        ActivityScenario.launch(MainActivity::class.java).use { scenario ->
            scenario.onActivity {
                assertTrue("Run this suite on a vehicle-sized window", it.resources.configuration.screenWidthDp >= 800)
                ViewModelProvider(it)[VoltroViewModel::class.java].setRoadMode(false)
            }
            SystemClock.sleep(700)
            scenario.onActivity { activity ->
                val texts = mutableListOf<TextView>()
                fun collect(view: View) {
                    if (view is TextView && view.text.isNotEmpty()) texts.add(view)
                    if (view is ViewGroup) for (i in 0 until view.childCount) collect(view.getChildAt(i))
                }
                collect(activity.findViewById(android.R.id.content))
                assertTrue(texts.size > 20)
                for (text in texts) assertTrue("Small vehicle text: ${text.text}",
                    text.textSize / activity.resources.displayMetrics.scaledDensity >= 21.9f)
                val history = texts.first { it.text.toString() == "주행 이력" }
                assertEquals("Header action must stay on one line", 1, history.lineCount)
                assertTrue(history.height >= 64 * activity.resources.displayMetrics.density)
            }
        }
    }
}
