package com.qqaazz0222.voltro

import android.content.res.Configuration
import androidx.core.graphics.ColorUtils
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.qqaazz0222.voltro.presentation.PleosDesign
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class DesignContrastTest {
    @Test fun dayAndNightContentHasAtLeastFourPointFiveContrast() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        for (night in listOf(Configuration.UI_MODE_NIGHT_NO, Configuration.UI_MODE_NIGHT_YES)) {
            val config = Configuration(context.resources.configuration)
            config.uiMode = config.uiMode and Configuration.UI_MODE_NIGHT_MASK.inv() or night
            val design = PleosDesign(context.createConfigurationContext(config))
            for ((text, background) in listOf(design.text to design.surface, design.secondaryText to design.surface,
                design.secondaryText to design.background, design.positive to design.surface,
                design.positive to design.selected, design.onFilled to design.filledButton,
                design.active to design.surface, design.warning to design.warningSurface)) {
                assertTrue("Insufficient contrast in night mode $night", ColorUtils.calculateContrast(text, background) >= 4.5)
            }
        }
    }
}
