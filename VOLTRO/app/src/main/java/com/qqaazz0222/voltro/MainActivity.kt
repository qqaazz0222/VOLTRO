package com.qqaazz0222.voltro

import android.app.AlertDialog
import android.content.Context
import android.content.res.ColorStateList
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.graphics.drawable.RippleDrawable
import android.os.Bundle
import android.text.InputType
import android.view.Gravity
import android.view.View
import android.view.inputmethod.InputMethodManager
import android.widget.*
import androidx.activity.ComponentActivity
import androidx.activity.OnBackPressedCallback
import androidx.activity.viewModels
import androidx.activity.result.contract.ActivityResultContracts
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowCompat
import androidx.appcompat.widget.SwitchCompat
import androidx.appcompat.content.res.AppCompatResources
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import com.qqaazz0222.voltro.domain.model.*
import com.qqaazz0222.voltro.domain.usecase.metrics
import com.qqaazz0222.voltro.presentation.*
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import kotlin.math.*

class MainActivity : ComponentActivity() {
    private val vm: VoltroViewModel by viewModels()
    private val design by lazy { PleosDesign(this) }
    private val ink get() = design.background
    private val panel get() = design.surface
    private val muted get() = design.secondaryText
    private val white get() = design.text
    private val accent get() = design.positive
    private val line get() = design.border
    private var query = ""
    private var pendingServerAction: (() -> Unit)? = null
    private val serverPermission = registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        val action = pendingServerAction; pendingServerAction = null
        if (granted) action?.invoke() else vm.serverPermissionDenied()
    }
    private lateinit var root: LinearLayout
    private var currentScroll: ScrollView? = null
    private var renderedScreen: Screen? = null
    private val wide get() = resources.configuration.screenWidthDp >= 800

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        WindowCompat.getInsetsController(window, window.decorView).let {
            it.isAppearanceLightStatusBars = !design.dark
            it.isAppearanceLightNavigationBars = !design.dark
        }
        query = savedInstanceState?.getString("query").orEmpty()
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (vm.state.value.driving != null) confirmStop() else vm.home()
            }
        })
        lifecycleScope.launch { repeatOnLifecycle(Lifecycle.State.STARTED) { vm.state.collect { render(it) } } }
    }
    override fun onSaveInstanceState(outState: Bundle) { outState.putString("query", query); super.onSaveInstanceState(outState) }
    override fun onStop() {
        if (vm.state.value.driving?.paused == false) vm.pauseForBackground()
        super.onStop()
    }

    private fun render(state: AppState) {
        val scrollY = if (renderedScreen == state.screen) currentScroll?.scrollY ?: 0 else 0
        renderedScreen = state.screen
        root = column().apply {
            setBackgroundColor(ink); isFocusableInTouchMode = true
            setPadding(dp(24), dp(12), dp(24), dp(12))
        }
        ViewCompat.setOnApplyWindowInsetsListener(root) { view, insets ->
            val bars = insets.getInsets(WindowInsetsCompat.Type.systemBars() or WindowInsetsCompat.Type.displayCutout())
            view.setPadding(bars.left + dp(24), bars.top + dp(12), bars.right + dp(24), bars.bottom + dp(12))
            insets
        }
        setContentView(root)
        ViewCompat.requestApplyInsets(root)
        root.addView(header(state))
        notice(state)?.let { root.addView(it) }
        val scroll = ScrollView(this).apply { isFillViewport = true; isVerticalScrollBarEnabled = false }
        currentScroll = scroll
        val body = column().apply { setPadding(0, dp(18), 0, dp(16)) }
        scroll.addView(body)
        root.addView(scroll, LinearLayout.LayoutParams(-1, 0, 1f))
        when (state.screen) {
            Screen.HOME -> home(body, state)
            Screen.COMPARISON -> comparison(body, state)
            Screen.DRIVING -> driving(body, state)
            Screen.REPORT -> report(body, state)
            Screen.HISTORY -> history(body, state)
        }
        when (state.screen) {
            Screen.HOME -> root.addView(button(if (state.busy) "분석 중…" else "경로 분석하기  →", primary = true, enabled = !state.busy) {
                hideKeyboard(); if (state.serverMode) withServerAccess { vm.analyze(query) } else vm.analyze(query)
            }.apply { id = R.id.analyze_routes })
            Screen.COMPARISON -> root.addView(button(if (state.busy) "처리 중…" else "선택한 경로로 Mock 주행  →", true,
                !state.busy && state.selectedId != null) { vm.startDriving() }.apply { id = R.id.start_trip })
            Screen.REPORT -> root.addView(button("새로운 여정 시작하기  →", true, !state.busy) { query = ""; vm.home() })
            Screen.HISTORY -> root.addView(button("목적지 검색으로 돌아가기", true) { vm.home() })
            Screen.DRIVING -> Unit
        }
        scroll.post { scroll.scrollTo(0, scrollY) }
    }

    private fun header(state: AppState): View {
        val bar = row().apply {
        gravity = Gravity.CENTER_VERTICAL
        addView(icon(R.drawable.ic_voltro), LinearLayout.LayoutParams(dp(48), dp(64)))
        addView(text("VOLTRO", 23f, white, true).apply { letterSpacing = .08f }, LinearLayout.LayoutParams(0, -2, 1f))
        addView(badge("●  MOCK", accent))
        if (wide) {
            addView(button(if (wide) "주행 이력" else "이력", enabled = state.driving == null && !state.busy) { vm.history() },
                LinearLayout.LayoutParams(dp(if (wide) 156 else 68), dp(64)).apply { marginStart = dp(12) })
            addView(button("설정", enabled = state.driving == null && !state.busy) { settings(state) },
                LinearLayout.LayoutParams(dp(if (wide) 126 else 68), dp(64)).apply { marginStart = dp(8) })
        }
        }
        if (wide || state.driving != null) return bar
        return column().apply {
            addView(bar)
            addView(row().apply {
                addView(button("주행 이력", enabled = !state.busy) { vm.history() }, LinearLayout.LayoutParams(0, dp(64), 1f))
                addView(button("설정", enabled = !state.busy) { settings(state) }, LinearLayout.LayoutParams(0, dp(64), 1f).apply { marginStart = dp(12) })
            }, margin(top = 10))
        }
    }

    private fun notice(state: AppState): View? {
        val message = state.error ?: state.message ?: return null
        return row().apply {
            gravity = Gravity.CENTER_VERTICAL
            background = shape(if (state.error != null) design.warningSurface else panel, 12)
            setPadding(dp(14), dp(8), dp(6), dp(8))
            addView(text(message, 18f, if (state.error != null) design.warning else white), LinearLayout.LayoutParams(0, -2, 1f))
            addView(button("닫기") { vm.clearNotice() }, LinearLayout.LayoutParams(dp(60), dp(48)))
        }
    }

    private fun home(body: LinearLayout, state: AppState) {
        body.addView(text("에너지 경로 도우미", 18f, muted))
        body.addView(text("시간과 배터리를 함께 비교하세요", if (wide) 36f else 28f, white, true), margin(bottom = 12, top = 8))
        val content = if (wide) row() else column()
        val planning = card()
        planning.addView(text("어디로 떠나시나요?", 23f, white, true), margin(bottom = 18))
        planning.addView(text("출발  ●  서울 시청", 14f, muted), margin(bottom = 16))
        val input = EditText(this).apply {
            id = R.id.destination_input
            setSingleLine(true); textSize = 18f; setTextColor(white); setHintTextColor(muted)
            hint = "목적지 검색 · 예: 강릉"
            setPadding(dp(16), dp(14), dp(16), dp(14)); background = shape(ink, 12, line)
            typeface = design.font; setText(query); contentDescription = "데모 목적지 검색"
            addTextChangedListener(object : android.text.TextWatcher {
                override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) = Unit
                override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) { query = s.toString() }
                override fun afterTextChanged(s: android.text.Editable?) = Unit
            })
            setOnEditorActionListener { _, _, _ ->
                hideKeyboard(); if (state.serverMode) withServerAccess { vm.analyze(query) } else vm.analyze(query); true
            }
        }
        planning.addView(input, margin(bottom = 20))
        planning.addView(text("추천 데모 목적지", 12f, muted, true), margin(bottom = 8))
        vm.destinations.forEachIndexed { index, destination ->
            val item = row().apply {
                gravity = Gravity.CENTER_VERTICAL; minimumHeight = dp(68)
                background = RippleDrawable(ColorStateList.valueOf(design.ripple), shape(if (state.destination?.id == destination.id) design.selected else panel, 12), null)
                setPadding(dp(10), dp(8), dp(8), dp(8))
                addView(text("0${index + 1}", 13f, accent, true), LinearLayout.LayoutParams(dp(36), -2))
                addView(column().apply {
                    addView(text(destination.name, 18f, white, true))
                    addView(text(destination.description, 12f, muted), margin(top = 4))
                }, LinearLayout.LayoutParams(0, -2, 1f))
                addView(icon(R.drawable.ic_chevron), LinearLayout.LayoutParams(dp(48), dp(48)))
                isClickable = true; isFocusable = true; contentDescription = "${destination.name} 선택"
                setOnClickListener { query = destination.name; hideKeyboard(); vm.selectDestination(destination) }
            }
            planning.addView(item, margin(bottom = 6))
        }
        val vehicle = card()
        vehicle.addView(row().apply {
            addView(text("MY ENERGY", 12f, muted, true), LinearLayout.LayoutParams(0, -2, 1f))
            addView(badge(when (state.vehicle.source) { DataSource.PLEOS -> "Pleos SOC"; DataSource.USER_INPUT -> "사용자 입력"; else -> "Demo EV" }, accent))
        })
        vehicle.addView(BatteryGaugeView(this, state.vehicle.socPercent), LinearLayout.LayoutParams(-1, dp(if (wide) 204 else 180)))
        vehicle.addView(text("출발할 준비가 되었어요", 21f, white, true).apply { gravity = Gravity.CENTER }, margin(bottom = 20))
        vehicle.addView(row().apply {
            addView(metric("평균 전비", f(state.vehicle.efficiencyKmPerKwh), "km/kWh"), LinearLayout.LayoutParams(0, -2, 1f))
            addView(metric("사용 가능 용량", f(state.vehicle.usableBatteryCapacityKwh, 0), "kWh"), LinearLayout.LayoutParams(0, -2, 1f))
        }, margin(bottom = 16))
        vehicle.addView(divider())
        vehicle.addView(text("최소 도착 잔량 ${f(state.preferences.minArrivalSoc, 0)}%  ·  추가 시간 ${f(state.preferences.maxExtraMinutes, 0)}분 이내", 13f, muted), margin(top = 16, bottom = 8))
        vehicle.addView(text(if (state.serverMode) "●  개발 서버로 분석 · Mock 데이터" else "●  오프라인 데모 · 서버 없이 실행", 13f, accent), margin(bottom = 4))
        vehicle.addView(text(if (state.vehicle.source == DataSource.PLEOS)
            "SOC: SDK 스냅샷 · 전비: ${if (state.vehicle.efficiencySource == DataSource.PLEOS) "SDK" else "설정값"} · 용량: 설정값"
            else "차량값은 데모 설정값입니다.", 12f, muted))
        vehicle.addView(text("경로·주행은 실제 도로가 아닌 시뮬레이션입니다.", 12f, muted), margin(top = 6))
        vehicle.addView(button(if (state.busy) "처리 중…" else "Pleos 차량 상태 읽기", enabled = !state.busy) { vm.readPleosVehicle() }, margin(top = 16))
        addPanels(content, planning, vehicle)
        body.addView(content)
        if (state.comparison != null) body.addView(button("마지막 경로 분석 보기", enabled = !state.busy) { vm.previousComparison() }, margin(top = 16))
        body.addView(text("YOUR ROUTE. YOUR ENERGY.", 10f, muted, true).apply { letterSpacing = .18f }, margin(top = 22))
    }

    private fun comparison(body: LinearLayout, state: AppState) {
        val comparison = state.comparison ?: return
        body.addView(text("경로의 기준에, 에너지를 더하다.", 28f, white, true), margin(bottom = 8))
        body.addView(text("서울 시청  →  ${comparison.destination.name}  ·  ${if (comparison.remote) "서버 분석" else "오프라인 분석"}", 15f, muted), margin(bottom = 20))
        val content = if (wide) row() else column()
        val visual = card()
        visual.addView(row().apply {
            addView(text("ROUTE OVERVIEW", 11f, muted, true), LinearLayout.LayoutParams(0, -2, 1f)); addView(badge("모식도", muted))
        })
        visual.addView(RouteMapView(this, comparison.routes, state.selectedId), LinearLayout.LayoutParams(-1, dp(if (wide) 270 else 220)))
        visual.addView(text("경로 좌표 기반 데모 모식도 · 실제 내비게이션 지도 아님", 12f, muted), margin(bottom = 14))
        val fastest = comparison.routes.minBy { it.durationMinutes }
        val selected = comparison.routes.firstOrNull { it.id == state.selectedId }
        val saving = selected?.let { fastest.energyKwh - it.energyKwh } ?: 0.0
        if (selected != null && saving > 0.001) {
            visual.addView(text("${f(saving)} kWh 덜 쓰는 여정", 24f, accent, true), margin(bottom = 6))
            visual.addView(text("빠른 경로 대비 ${f(selected.durationMinutes - fastest.durationMinutes, 0)}분 추가 · 도착 잔량 ${f(selected.arrivalSoc)}%", 14f, white))
        } else visual.addView(text("시간과 소비량을 비교해 경로를 선택하세요.", 16f, white))
        val choices = column()
        if (comparison.recommendedId == null) choices.addView(text("조건을 만족하는 추천 경로가 없습니다.", 18f, design.warning), margin(bottom = 10))
        comparison.routes.forEach { route ->
            val safe = route.arrivalSoc >= state.preferences.minArrivalSoc
            val active = state.selectedId == route.id
            val option = card().apply {
                background = RippleDrawable(ColorStateList.valueOf(design.ripple), shape(if (active) design.selected else panel, 16, if (active) accent else line), null)
                alpha = if (safe) 1f else .55f; isClickable = safe; isFocusable = safe; contentDescription = "${route.label} 선택"
                if (safe) setOnClickListener { vm.selectRoute(route.id) }
            }
            option.addView(row().apply {
                addView(text("${if (active) "●" else "○"}  ${route.label}", 19f, if (active) accent else white, true), LinearLayout.LayoutParams(0, -2, 1f))
                if (route.id == comparison.recommendedId) addView(badge("추천", accent))
            }, margin(bottom = 10))
            option.addView(row().apply {
                addView(text("${f(route.durationMinutes, 0)}분", 24f, white, true), LinearLayout.LayoutParams(0, -2, 1f))
                addView(text("${f(route.energyKwh)} kWh", 24f, if (active) accent else white, true))
            }, margin(bottom = 8))
            option.addView(text("${f(route.distanceKm)} km   ·   도착 ${f(route.arrivalSoc)}%   ·   ${route.roadName}", 13f, muted))
            if (!safe) option.addView(text("최소 도착 잔량 미달 · 선택 불가", 18f, design.warning), margin(top = 6))
            choices.addView(option, margin(bottom = 10))
        }
        addPanels(content, visual, choices); body.addView(content)
        body.addView(button("← 목적지 다시 선택", enabled = !state.busy) { vm.home() }, margin(top = 12))
    }

    private fun driving(body: LinearLayout, state: AppState) {
        val d = state.driving ?: return
        val route = d.activeRoute
        val metrics = d.metrics(state.vehicle)
        val soc = metrics.currentSoc
        val remaining = metrics.remainingKm
        val minutes = metrics.remainingMinutes
        val arrival = metrics.arrivalSoc
        body.addView(text("${state.comparison?.destination?.name}까지, 효율적으로.", 28f, white, true), margin(bottom = 8))
        body.addView(text("${route.label}  ·  ${if (d.paused) "데모 일시정지" else "Mock 주행 중"}  ·  ${d.speed}× 재생", 15f, accent), margin(bottom = 20))
        val content = if (wide) row() else column()
        val visual = card()
        visual.addView(RouteMapView(this, listOf(route), route.id, d.position), LinearLayout.LayoutParams(-1, dp(if (wide) 260 else 190)))
        visual.addView(text("${f(d.distanceKm)} / ${f(route.distanceKm)} km", 14f, muted), margin(top = 8, bottom = 12))
        visual.addView(ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal).apply {
            max = 1000; progress = (d.distanceKm / route.distanceKm * 1000).toInt()
            progressTintList = ColorStateList.valueOf(accent); progressBackgroundTintList = ColorStateList.valueOf(line)
            contentDescription = "주행 진행률"
        }, LinearLayout.LayoutParams(-1, dp(6)))
        visual.addView(text("좌표 순차 재생 · 위치 정확도 5 m (Mock)", 12f, muted), margin(top = 14))
        val info = card()
        info.addView(text("남은 여정", 13f, muted, true), margin(bottom = 12))
        info.addView(text("${f(minutes, 0)}분", 48f, white, true), margin(bottom = 8))
        info.addView(text("${f(remaining)} km 남음", 20f, white), margin(bottom = 24)); info.addView(divider())
        info.addView(row().apply {
            addView(metric("현재 배터리", f(soc), "%"), LinearLayout.LayoutParams(0, -2, 1f))
            addView(metric("예상 도착 잔량", f(arrival), "%"), LinearLayout.LayoutParams(0, -2, 1f))
        }, margin(top = 18, bottom = 18))
        info.addView(text("${f(d.consumedKwh)} kWh 소비 · 시뮬레이션 계산값", 13f, muted))
        addPanels(content, visual, info)
        d.advice?.let { advice ->
            val decision = card().apply { background = shape(design.selected, 16, accent) }
            decision.addView(text("↖  전방 ${f(advice.distanceMeters / 1000)} km 분기점", 18f, white, true), margin(bottom = 8))
            decision.addView(text("${f(advice.savingKwh)} kWh 절약 · ${f(advice.additionalMinutes, 0)}분 추가", 28f, accent, true), margin(bottom = 6))
            decision.addView(text("도착 잔량 ${f(advice.arrivalSoc)}% · 선택할 동안 데모가 일시정지됩니다.", 14f, muted), margin(bottom = 12))
            decision.addView(row().apply {
                addView(button("기존 경로 유지") { vm.dismissAdvice() }, LinearLayout.LayoutParams(0, dp(64), 1f))
                addView(button("절전 경로로 변경", true, !state.busy) { vm.acceptAdvice() }, LinearLayout.LayoutParams(0, dp(64), 1f).apply { marginStart = dp(12) })
            })
            body.addView(decision, margin(top = 16))
        }
        body.addView(content, margin(top = if (d.advice != null) 16 else 0))
        body.addView(row().apply {
            addView(button(if (d.paused) "데모 계속" else "일시정지", enabled = !state.busy) { vm.togglePause() }, LinearLayout.LayoutParams(0, dp(64), 1f))
            addView(button("배속 ${d.speed}×", enabled = !state.busy) { vm.changeSpeed() }, LinearLayout.LayoutParams(0, dp(64), 1f).apply { marginStart = dp(10) })
            addView(button("주행 취소", enabled = !state.busy) { confirmStop() }, LinearLayout.LayoutParams(0, dp(64), 1f).apply { marginStart = dp(10) })
        }, margin(top = 16))
        body.addView(text("데모 전용 화면 · 실제 차량 내비게이션은 변경하지 않습니다.", 12f, muted), margin(top = 12))
    }

    private fun report(body: LinearLayout, state: AppState) {
        val report = state.report ?: return
        body.addView(text("여정은 끝나도, 에너지는 남도록.", 28f, white, true), margin(bottom = 8))
        body.addView(text("${report.destination} 도착 · ${report.routeLabel} · MOCK 리포트", 15f, muted), margin(bottom = 24))
        val summary = card()
        summary.addView(text("SIMULATED TRIP", 11f, accent, true), margin(bottom = 12))
        summary.addView(text("${f(report.simulatedEnergyKwh)} kWh", 44f, accent, true), margin(bottom = 8))
        summary.addView(text("시뮬레이션 소비량 · SOC 차이 × 배터리 용량", 14f, muted), margin(bottom = 24))
        summary.addView(row().apply {
            addView(metric("총 주행 거리", f(report.distanceKm), "km"), LinearLayout.LayoutParams(0, -2, 1f))
            addView(metric("가상 주행 시간", f(report.durationMinutes, 0), "분"), LinearLayout.LayoutParams(0, -2, 1f))
            if (wide) addView(metric("도착 배터리", f(report.finalSoc), "%"), LinearLayout.LayoutParams(0, -2, 1f))
        }, margin(bottom = 20)); summary.addView(divider())
        listOf("출발 시 예상 소비량" to "${f(report.estimatedEnergyKwh)} kWh",
            "배터리 변화" to "${f(report.initialSoc)}% → ${f(report.finalSoc)}% (${f(report.initialSoc - report.finalSoc)}%p)",
            "실측 소비량" to "측정되지 않음", "예측 오차" to "실측 데이터가 없어 계산하지 않음").forEach { (label, value) ->
            summary.addView(row().apply {
                gravity = Gravity.CENTER_VERTICAL
                addView(text(label, 15f, muted), LinearLayout.LayoutParams(0, -2, 1f))
                addView(text(value, if (wide) 16f else 13f, white, true))
            }, margin(top = 18))
        }
        body.addView(summary)
        body.addView(text("경로 변경 시 출발 예측과 완료 경로가 달라질 수 있습니다. 이 차이는 예측 정확도나 실차 절약 성능을 뜻하지 않습니다.", 13f, muted), margin(top = 16, bottom = 12))
        body.addView(text(if (report.remote) {
            if (report.synced) "●  기기 저장 및 개발 서버 저장 완료" else "○  개발 서버 저장 대기 · 다시 저장할 수 있습니다."
        } else "●  기기에 저장 · 최근 50개 주행", 13f, accent), margin(bottom = 12))
        body.addView(row().apply {
            addView(button("주행 이력") { vm.history() }, LinearLayout.LayoutParams(0, dp(64), 1f))
            addView(button("리포트 다시 저장", enabled = !state.busy) { vm.syncReport() }, LinearLayout.LayoutParams(0, dp(64), 1f).apply { marginStart = dp(12) })
        })
    }

    private fun history(body: LinearLayout, state: AppState) {
        body.addView(text("지나온 여정의 에너지.", 28f, white, true), margin(bottom = 8))
        body.addView(text("이 기기에 저장된 최근 50개 주행 · 정밀 위치 이력은 저장하지 않습니다.", 14f, muted), margin(bottom = 24))
        if (state.history.isEmpty()) body.addView(card().apply {
            addView(text("아직 기록된 여정이 없습니다.", 22f, white, true), margin(bottom = 12))
            addView(text("목적지를 선택하고 Mock 주행을 완료해 보세요.", 15f, muted))
        })
        state.history.forEach { record ->
            body.addView(card().apply {
                addView(row().apply {
                    addView(text(record.destination, 21f, white, true), LinearLayout.LayoutParams(0, -2, 1f))
                    addView(text("${f(record.simulatedEnergyKwh)} kWh  ↗", 22f, accent, true))
                }, margin(bottom = 8))
                addView(text("${SimpleDateFormat("MM.dd HH:mm", Locale.KOREA).format(Date(record.endedAt))}  ·  ${record.routeLabel}  ·  ${f(record.distanceKm)} km  ·  MOCK", 13f, muted))
                isClickable = true; isFocusable = true; setOnClickListener { vm.openReport(record) }
            }, margin(bottom = 12))
        }
        if (state.history.isNotEmpty()) body.addView(button("기기 주행 이력 삭제") {
            AlertDialog.Builder(this).setTitle("주행 이력을 삭제할까요?").setMessage("이 기기의 기록을 모두 삭제합니다. 개발 서버의 기록은 별도로 관리됩니다.")
                .setNegativeButton("취소", null).setPositiveButton("삭제") { _, _ -> vm.deleteHistory() }.show()
        })
    }

    private fun settings(state: AppState) {
        val fields = column().apply { setPadding(dp(24), dp(8), dp(24), dp(16)) }
        fun field(label: String, value: Double): EditText {
            fields.addView(text(label, 14f, muted), margin(top = 12, bottom = 4))
            return EditText(this).apply {
                inputType = InputType.TYPE_CLASS_NUMBER or InputType.TYPE_NUMBER_FLAG_DECIMAL
                setSingleLine(true); setText(f(value)); setTextColor(white); setSelectAllOnFocus(true)
                fields.addView(this, LinearLayout.LayoutParams(-1, dp(52)))
            }
        }
        val soc = field("출발 배터리 SOC (0–100%)", state.vehicle.socPercent)
        val efficiency = field("평균 전비 (0 초과, km/kWh)", state.vehicle.efficiencyKmPerKwh)
        val capacity = field("사용 가능 배터리 용량 (0 초과, kWh)", state.vehicle.usableBatteryCapacityKwh)
        val minimum = field("최소 도착 잔량 (0–100%)", state.preferences.minArrivalSoc)
        val extra = field("허용 추가 시간 (0–120분)", state.preferences.maxExtraMinutes)
        val server = SwitchCompat(this).apply { text = "개발 서버 사용 (10.0.2.2:8000)"; setTextColor(white); isChecked = state.serverMode; minimumHeight = dp(64) }
        val developerBuild = applicationInfo.flags and android.content.pm.ApplicationInfo.FLAG_DEBUGGABLE != 0
        server.isEnabled = developerBuild
        val failure = SwitchCompat(this).apply { text = "경로 변경 실패 시나리오"; setTextColor(white); isChecked = state.failRouteChange; minimumHeight = dp(64) }
        fields.addView(server, margin(top = 12)); fields.addView(failure)
        fields.addView(button("서버 연결 확인", enabled = developerBuild) { withServerAccess { vm.checkServer() } })
        fields.addView(text("모든 주행은 시뮬레이션입니다. Pleos 실차 연결과 음성 안내는 SDK·정책 검증 전 비활성화됩니다.", 13f, muted), margin(top = 12))
        val error = text("", 18f, design.warning); fields.addView(error, margin(top = 12))
        val dialog = AlertDialog.Builder(this).setTitle("에너지 & 데모 설정")
            .setView(ScrollView(this).apply { addView(fields) }).setNegativeButton("취소", null).setPositiveButton("적용", null).create()
        dialog.setOnShowListener {
            dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener {
                if (vm.state.value.busy) { error.text = "서버 확인이 끝난 뒤 적용하세요."; return@setOnClickListener }
                try {
                    val s = soc.text.toString().toDouble(); val e = efficiency.text.toString().toDouble(); val c = capacity.text.toString().toDouble()
                    require(e <= 30 && c <= 300)
                    vm.configure(minimum.text.toString().toDouble(), extra.text.toString().toDouble(), s, e, c, server.isChecked, failure.isChecked)
                    dialog.dismiss()
                } catch (_: Exception) { error.text = "숫자와 입력 범위를 확인하세요. 전비는 30, 용량은 300 이하입니다." }
            }
        }
        dialog.show()
    }
    private fun confirmStop() {
        AlertDialog.Builder(this).setTitle("Mock 주행을 취소할까요?").setMessage("진행 중인 시뮬레이션을 종료합니다.")
            .setNegativeButton("계속 주행", null).setPositiveButton("주행 취소") { _, _ -> vm.stopDriving() }.show()
    }
    private fun withServerAccess(action: () -> Unit) {
        val permission = "android.permission.ACCESS_LOCAL_NETWORK"
        if (Build.VERSION.SDK_INT >= 37 && checkSelfPermission(permission) != PackageManager.PERMISSION_GRANTED) {
            pendingServerAction = action; serverPermission.launch(permission)
        } else action()
    }
    private fun hideKeyboard() { (getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager).hideSoftInputFromWindow(currentFocus?.windowToken, 0) }
    private fun dp(value: Int) = (value * resources.displayMetrics.density).roundToInt()
    private fun f(value: Double, digits: Int = 1) = String.format(Locale.US, "%.${digits}f", value)
    private fun column() = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
    private fun row() = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
    private fun text(value: String, size: Float, color: Int = white, bold: Boolean = false) = TextView(this).apply {
        text = value; textSize = size.coerceAtLeast(18f); setTextColor(color); includeFontPadding = false
        typeface = if (bold) design.boldFont else design.font
    }
    private fun shape(color: Int, radius: Int, stroke: Int? = null) = GradientDrawable().apply {
        setColor(color); cornerRadius = dp(radius).toFloat(); stroke?.let { setStroke(dp(1), it) }
    }
    private fun card() = column().apply { background = shape(panel, 18); setPadding(dp(22), dp(22), dp(22), dp(22)) }
    private fun badge(value: String, color: Int) = text(value, 11f, color, true).apply {
        background = shape(panel, 8, line); setPadding(dp(12), dp(8), dp(12), dp(8))
    }
    private fun metric(label: String, value: String, unit: String) = column().apply {
        addView(text(label, 12f, muted), margin(bottom = 10)); addView(text(value, if (wide) 30f else 25f, white, true), margin(bottom = 4)); addView(text(unit, 12f, muted))
    }
    private fun divider() = View(this).apply { setBackgroundColor(line); layoutParams = LinearLayout.LayoutParams(-1, dp(1)) }
    private fun margin(top: Int = 0, bottom: Int = 0) = LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(top); bottomMargin = dp(bottom) }
    private fun button(value: String, primary: Boolean = false, enabled: Boolean = true, action: () -> Unit) = Button(this).apply {
        text = value; textSize = if (wide) 22f else 18f; typeface = design.boldFont; isAllCaps = false
        minHeight = dp(64); minimumHeight = dp(64)
        setTextColor(if (primary) design.onFilled else white)
        background = RippleDrawable(ColorStateList.valueOf(design.ripple), shape(if (primary) design.filledButton else design.button, 12), null)
        val iconId = when (value) { "주행 이력" -> R.drawable.ic_history; "설정" -> R.drawable.ic_settings; else -> null }
        iconId?.let { resource ->
            val drawable = AppCompatResources.getDrawable(this@MainActivity, resource)!!.mutate()
            drawable.setTint(white); drawable.setBounds(0, 0, dp(32), dp(32))
            setCompoundDrawablesRelative(drawable, null, null, null); compoundDrawablePadding = dp(8)
        }
        setPadding(dp(16), dp(10), dp(16), dp(10)); isEnabled = enabled; alpha = if (enabled) 1f else .4f
        setOnClickListener { performHapticFeedback(android.view.HapticFeedbackConstants.VIRTUAL_KEY); action() }
    }
    private fun icon(drawable: Int) = ImageView(this).apply {
        setImageResource(drawable); imageTintList = ColorStateList.valueOf(white)
        importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_NO
    }
    private fun addPanels(container: LinearLayout, first: View, second: View) {
        if (wide) {
            container.addView(first, LinearLayout.LayoutParams(0, -2, 1f))
            container.addView(second, LinearLayout.LayoutParams(0, -2, 1f).apply { marginStart = dp(20) })
        } else { container.addView(first, margin(bottom = 16)); container.addView(second, margin()) }
    }
}
