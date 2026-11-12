package com.qqaazz0222.voltro.presentation

import android.app.AlertDialog
import android.content.Context
import android.content.Intent
import android.graphics.*
import android.net.Uri
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.widget.*
import com.qqaazz0222.voltro.data.road.MapTileStore
import com.qqaazz0222.voltro.domain.model.*
import com.qqaazz0222.voltro.domain.usecase.MapProjection
import kotlin.math.*

class RoadMapCamera {
    var key = ""
    var centerX = .5; var centerY = .5
    var zoom = 0
}

class RoadMapPanel(context: Context, routes: List<RouteCandidate>, selected: String?, position: GeoPoint?,
                   camera: RoadMapCamera, key: String, interactive: Boolean) : FrameLayout(context) {
    private val map = RoadMapView(context, routes, selected, position, camera, key, interactive)
    private val design = PleosDesign(context)
    private fun dp(n: Int) = (n * resources.displayMetrics.density).roundToInt()
    init {
        addView(map, LayoutParams(-1, -1))
        val status = TextView(context).apply {
            textSize = 18f; typeface = design.font; setTextColor(design.text); setBackgroundColor(design.surface)
            setPadding(dp(6), dp(4), dp(6), dp(4)); maxWidth = dp(250)
            if (interactive) setOnClickListener { MapTileStore.get(context).retry(); map.invalidate() }
        }
        addView(status, LayoutParams(-2, -2, Gravity.TOP or Gravity.START))
        map.statusChanged = { message ->
            if (status.text.toString() != message) { status.text = message; status.visibility = if (message.isEmpty()) GONE else VISIBLE }
        }
        val attribution = TextView(context).apply {
            text = "© OpenStreetMap contributors · OSRM"; textSize = 18f; typeface = design.font
            setTextColor(design.text); setBackgroundColor(design.surface); setPadding(dp(6), dp(5), dp(6), dp(5))
            if (interactive) setOnClickListener {
                val urls = listOf("https://www.openstreetmap.org/copyright", "https://routing.openstreetmap.de/about.html", "https://www.openstreetmap.org/fixthemap")
                AlertDialog.Builder(context).setTitle("지도와 도로 경로 출처")
                    .setItems(arrayOf("OpenStreetMap 저작권과 ODbL", "OSRM 경로 서비스", "지도 오류 신고")) { _, index ->
                        runCatching { context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(urls[index]))) }
                    }.setNegativeButton("닫기", null).show()
            }
        }
        addView(attribution, LayoutParams(-2, -2, Gravity.BOTTOM or Gravity.START))
        if (interactive) {
            val controls = LinearLayout(context).apply { orientation = LinearLayout.VERTICAL }
            listOf("+" to { map.zoomBy(1) }, "−" to { map.zoomBy(-1) }, "전체" to { map.fit() }).forEach { (label, action) ->
                controls.addView(Button(context).apply {
                    text = label; textSize = if (label == "전체") 18f else 24f; typeface = design.font
                    setTextColor(design.text); contentDescription = when (label) { "+" -> "지도 확대"; "−" -> "지도 축소"; else -> "전체 경로 보기" }
                    minWidth = 0; minimumWidth = 0; setPadding(0, 0, 0, 0); setOnClickListener { action() }
                }, LinearLayout.LayoutParams(dp(48), dp(48)))
            }
            addView(controls, LayoutParams(dp(48), -2, Gravity.TOP or Gravity.END))
        }
    }
}

/** Native Web Mercator viewport. Only real OSRM geometry is accepted here. */
class RoadMapView(context: Context, private val routes: List<RouteCandidate>, private val selected: String?,
                  private val position: GeoPoint?, private val camera: RoadMapCamera, private val mapKey: String,
                  private val interactive: Boolean) : View(context) {
    private val paint = Paint(Paint.ANTI_ALIAS_FLAG or Paint.FILTER_BITMAP_FLAG)
    private val design = PleosDesign(context)
    private val tiles = MapTileStore.get(context)
    private val scale = resources.displayMetrics.density
    private val tileScale = scale * if (resources.configuration.screenWidthDp >= 800) 1.5f else 1f
    private val projected = routes.associate { r -> r.id to r.nodes.map { MapProjection.project(it.point) } }
    private var visibleKeys: Set<String> = emptySet()
    private var lastX = 0f; private var lastY = 0f
    var statusChanged: ((String) -> Unit)? = null
    init {
        require(routes.isNotEmpty() && routes.all { it.source == RouteSource.OSRM })
        contentDescription = "OpenStreetMap 실제 지도와 OSRM 도로 경로 ${routes.size}개"
        isFocusable = interactive
    }
    fun wants(key: String) = isAttachedToWindow && key in visibleKeys
    override fun onDetachedFromWindow() { visibleKeys = emptySet(); super.onDetachedFromWindow() }
    override fun onSizeChanged(w: Int, h: Int, oldw: Int, oldh: Int) {
        if (camera.key != mapKey || camera.zoom == 0) fit()
    }
    fun fit() {
        if (width <= 0 || height <= 0) return
        val all = projected.values.flatten()
        val x1 = all.minOf { it.first }; val x2 = all.maxOf { it.first }
        val y1 = all.minOf { it.second }; val y2 = all.maxOf { it.second }
        camera.centerX = (x1 + x2) / 2; camera.centerY = (y1 + y2) / 2
        val roomX = max(40f, width - 100 * scale); val roomY = max(40f, height - 96 * scale)
        camera.zoom = floor(log2(min(roomX / (256 * tileScale * max(x2 - x1, 1e-7)), roomY / (256 * tileScale * max(y2 - y1, 1e-7))))).toInt().coerceIn(2, 18)
        camera.key = mapKey; invalidate()
    }
    fun zoomBy(delta: Int) { camera.zoom = (camera.zoom + delta).coerceIn(2, 18); invalidate() }
    override fun onTouchEvent(event: MotionEvent): Boolean {
        if (!interactive) return false
        when (event.actionMasked) {
            MotionEvent.ACTION_DOWN -> { lastX = event.x; lastY = event.y; parent.requestDisallowInterceptTouchEvent(true); return true }
            MotionEvent.ACTION_MOVE -> {
                val world = 256 * tileScale * 2.0.pow(camera.zoom)
                camera.centerX = (camera.centerX - (event.x - lastX) / world).coerceIn(0.0, 1.0)
                camera.centerY = (camera.centerY - (event.y - lastY) / world).coerceIn(0.0, 1.0)
                lastX = event.x; lastY = event.y; invalidate(); return true
            }
            MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> { parent.requestDisallowInterceptTouchEvent(false); performClick(); return true }
        }
        return true
    }
    override fun performClick(): Boolean { super.performClick(); return true }
    override fun onDraw(canvas: Canvas) {
        canvas.drawColor(design.background)
        if (camera.zoom == 0) return
        val tileSize = 256 * tileScale; val count = 1 shl camera.zoom
        val world = tileSize * count.toDouble()
        val left = camera.centerX * world - width / 2; val top = camera.centerY * world - height / 2
        val x1 = floor(left / tileSize).toInt(); val x2 = floor((left + width - 1) / tileSize).toInt()
        val y1 = floor(top / tileSize).toInt().coerceAtLeast(0); val y2 = floor((top + height - 1) / tileSize).toInt().coerceAtMost(count - 1)
        val viewport = (x1..x2).flatMap { x -> (y1..y2).map { y -> Triple(x, y, "${camera.zoom}/${Math.floorMod(x, count)}/$y") } }
        visibleKeys = viewport.map { it.third }.toSet()
        var missing = 0; var failed = false
        for ((x, y, key) in viewport) {
            val bitmap = tiles.tile(key, this)
            if (bitmap == null) { missing++; failed = failed || tiles.failed(key); continue }
            paint.style = Paint.Style.FILL; paint.color = Color.WHITE
            canvas.drawBitmap(bitmap, null, RectF((x * tileSize - left).toFloat(), (y * tileSize - top).toFloat(),
                ((x + 1) * tileSize - left).toFloat(), ((y + 1) * tileSize - top).toFloat()), paint)
        }
        fun point(p: Pair<Double, Double>) = PointF((p.first * world - left).toFloat(), (p.second * world - top).toFloat())
        for (route in routes.sortedBy { it.id == selected }) {
            val path = Path()
            projected.getValue(route.id).forEachIndexed { i, p -> point(p).let { if (i == 0) path.moveTo(it.x, it.y) else path.lineTo(it.x, it.y) } }
            paint.style = Paint.Style.STROKE; paint.strokeJoin = Paint.Join.ROUND; paint.strokeCap = Paint.Cap.ROUND
            paint.color = Color.WHITE; paint.strokeWidth = (if (route.id == selected) 7 else 5) * scale; canvas.drawPath(path, paint)
            paint.color = if (route.id == selected) Color.rgb(0, 100, 255) else Color.rgb(75, 82, 98)
            paint.strokeWidth = (if (route.id == selected) 4f else 2.5f) * scale; canvas.drawPath(path, paint)
        }
        paint.style = Paint.Style.FILL
        for (p in listOf(routes.first().nodes.first().point, routes.first().nodes.last().point)) {
            val at = point(MapProjection.project(p)); paint.color = Color.WHITE; canvas.drawCircle(at.x, at.y, 8 * scale, paint)
            paint.color = Color.rgb(19, 20, 23); canvas.drawCircle(at.x, at.y, 5 * scale, paint)
        }
        position?.let {
            val at = point(MapProjection.project(it))
            paint.color = 0x330064FF; canvas.drawCircle(at.x, at.y, 18 * scale, paint)
            paint.color = Color.WHITE; canvas.drawCircle(at.x, at.y, 10 * scale, paint)
            paint.color = Color.rgb(0, 100, 255); canvas.drawCircle(at.x, at.y, 7 * scale, paint)
        }
        statusChanged?.invoke(when { failed -> "지도 연결 실패 · 탭하여 재시도"; missing > 0 -> "지도 로딩 중…"; else -> "" })
    }
}
