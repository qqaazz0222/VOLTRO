package com.qqaazz0222.voltro.presentation

import android.content.Context
import android.graphics.*
import android.view.View
import com.qqaazz0222.voltro.domain.model.*
import kotlin.math.*

class BatteryGaugeView(context: Context, private val soc: Double) : View(context) {
    private val paint = Paint(Paint.ANTI_ALIAS_FLAG)
    private val design = PleosDesign(context)
    init { contentDescription = "현재 배터리 ${soc.toInt()}퍼센트" }
    override fun onDraw(canvas: Canvas) {
        val scale = resources.displayMetrics.density
        val radius = min(width / 2f - 24 * scale, height / 2f - 16 * scale)
        val cx = width / 2f; val cy = height / 2f
        val rect = RectF(cx - radius, cy - radius, cx + radius, cy + radius)
        paint.style = Paint.Style.STROKE; paint.strokeWidth = 9 * scale; paint.strokeCap = Paint.Cap.ROUND
        paint.color = design.border; canvas.drawArc(rect, 135f, 270f, false, paint)
        paint.color = design.active; canvas.drawArc(rect, 135f, 270f * soc.toFloat() / 100, false, paint)
        paint.style = Paint.Style.FILL; paint.typeface = design.boldFont
        paint.textAlign = Paint.Align.CENTER; paint.textSize = 46 * scale; paint.color = design.text
        canvas.drawText("${soc.toInt()}%", cx, cy + 8 * scale, paint)
        paint.textSize = 18 * scale; paint.typeface = design.font; paint.color = design.secondaryText
        canvas.drawText("배터리 잔량", cx, cy + 36 * scale, paint)
    }
}

/** Geographic schematic from scenario coordinates; no road tiles or turn guidance. */
class RouteMapView(context: Context, private val routes: List<RouteCandidate>, private val selected: String?,
                   private val position: GeoPoint? = null) : View(context) {
    private val paint = Paint(Paint.ANTI_ALIAS_FLAG)
    private val design = PleosDesign(context)
    init { contentDescription = "Mock 후보 경로 모식도"; importantForAccessibility = IMPORTANT_FOR_ACCESSIBILITY_NO }
    override fun onDraw(canvas: Canvas) {
        if (routes.isEmpty()) return
        val scale = resources.displayMetrics.density
        val all = routes.flatMap { it.nodes }.map { it.point }
        val minLat = all.minOf { it.latitude }; val maxLat = all.maxOf { it.latitude }
        val minLon = all.minOf { it.longitude }; val maxLon = all.maxOf { it.longitude }
        val pad = 28 * scale
        fun project(point: GeoPoint) = PointF(
            pad + ((point.longitude - minLon) / max(.001, maxLon - minLon)).toFloat() * (width - pad * 2),
            height - pad - ((point.latitude - minLat) / max(.001, maxLat - minLat)).toFloat() * (height - pad * 2))
        paint.color = design.border; paint.strokeWidth = scale
        var x = 0f
        while (x < width) { canvas.drawLine(x, 0f, x, height.toFloat(), paint); x += 32 * scale }
        var y = 0f
        while (y < height) { canvas.drawLine(0f, y, width.toFloat(), y, paint); y += 32 * scale }
        for (route in routes.sortedBy { it.id == selected }) {
            val active = route.id == selected
            val path = Path()
            route.nodes.forEachIndexed { index, node ->
                val p = project(node.point)
                if (index == 0) path.moveTo(p.x, p.y) else path.lineTo(p.x, p.y)
            }
            paint.style = Paint.Style.STROKE; paint.strokeJoin = Paint.Join.ROUND; paint.strokeCap = Paint.Cap.ROUND
            paint.strokeWidth = (if (active) 6 else 3) * scale
            paint.color = if (active) design.positive else design.secondaryText
            paint.pathEffect = if (active) null else DashPathEffect(floatArrayOf(8 * scale, 6 * scale), 0f)
            canvas.drawPath(path, paint)
        }
        paint.pathEffect = null
        paint.style = Paint.Style.FILL
        val start = project(routes.first().nodes.first().point); val end = project(routes.first().nodes.last().point)
        paint.color = design.text; canvas.drawCircle(start.x, start.y, 6 * scale, paint)
        paint.color = design.positive; canvas.drawCircle(end.x, end.y, 8 * scale, paint)
        paint.color = design.surface; canvas.drawCircle(end.x, end.y, 3 * scale, paint)
        paint.color = design.text; paint.textSize = 18 * scale; paint.typeface = design.font; paint.textAlign = Paint.Align.LEFT
        canvas.drawText("서울", start.x, start.y - 14 * scale, paint)
        paint.textAlign = Paint.Align.RIGHT; canvas.drawText("목적지", end.x, end.y + 25 * scale, paint)
        position?.let {
            val p = project(it)
            paint.color = (design.positive and 0x00FFFFFF) or 0x33000000; canvas.drawCircle(p.x, p.y, 18 * scale, paint)
            paint.color = design.surface; canvas.drawCircle(p.x, p.y, 10 * scale, paint)
            paint.color = design.positive; canvas.drawCircle(p.x, p.y, 6 * scale, paint)
        }
    }
}
