package com.qqaazz0222.voltro

import androidx.activity.ComponentActivity
import android.os.Bundle
import android.widget.TextView
import com.qqaazz0222.voltro.data.mock.MockVehicleRepository
import com.qqaazz0222.voltro.data.remote.BackendClient
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val vehicle = MockVehicleRepository().observeVehicleEnergyState().value
        val label = TextView(this).apply {
            text = "VOLTRO\nYour Route. Your Energy.\n\nMOCK · ${vehicle.socPercent}%\n${vehicle.efficiencyKmPerKwh} km/kWh"
            textSize = 28f
            setPadding(48, 64, 48, 32)
        }
        setContentView(label)
        lifecycleScope.launch {
            label.append(runCatching { BackendClient().request("/health"); "\n서버 연결됨" }
                .getOrDefault("\n오프라인 Mock 모드"))
        }
    }
}
