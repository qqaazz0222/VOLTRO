package com.qqaazz0222.voltro.presentation

import android.content.Context
import android.content.res.Configuration
import android.graphics.Color
import android.graphics.Typeface
import com.qqaazz0222.voltro.R

/** Local View implementation of the public Pleos foundations; not a Pleos SDK component. */
class PleosDesign(context: Context) {
    val dark = context.resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK == Configuration.UI_MODE_NIGHT_YES
    private fun color(light: String, night: String) = Color.parseColor(if (dark) night else light)
    val background = context.getColor(R.color.voltro_background)
    val surface = context.getColor(R.color.voltro_surface)
    val text = context.getColor(R.color.voltro_text)
    val secondaryText = context.getColor(R.color.voltro_secondary)
    val border = color("#E0E1E6", "#44464E")
    val button = color("#EDEEF2", "#44464E")
    val filledButton = context.getColor(R.color.voltro_filled)
    val onFilled = context.getColor(R.color.voltro_on_filled)
    val selected = color("#F3F6FF", "#283D59")
    val positive = context.getColor(R.color.voltro_positive)
    val active = context.getColor(R.color.voltro_active)
    val warning = color("#AD2B12", "#FFB49F")
    val warningSurface = color("#FFF0EC", "#4C302B")
    val ripple = color("#20000000", "#30FFFFFF")
    val font: Typeface = context.resources.getFont(R.font.asta_sans)
    val boldFont: Typeface = Typeface.create(font, 600, false)
}
