package com.qqaazz0222.voltro

import com.qqaazz0222.voltro.domain.usecase.EnergyEngine
import org.junit.Assert.*
import org.junit.Test

class EnergyEngineTest {
    @Test fun baselineAndUnreachableSoc() {
        assertEquals(24.0, EnergyEngine.predict(120.0, 5.0), 0.000001)
        assertEquals(33.714285714, EnergyEngine.arrivalSoc(68.0, 70.0, 24.0), 0.000001)
        assertEquals(0.0, EnergyEngine.predict(0.0, 5.0), 0.0)
        assertTrue(EnergyEngine.arrivalSoc(10.0, 70.0, 24.0) < 0)
    }
    @Test fun invalidInputsRejected() {
        listOf<() -> Any>(
            { EnergyEngine.predict(-1.0, 5.0) },
            { EnergyEngine.predict(1.0, 0.0) },
            { EnergyEngine.predict(Double.NaN, 5.0) },
            { EnergyEngine.arrivalSoc(68.0, 0.0, 1.0) },
            { EnergyEngine.arrivalSoc(101.0, 70.0, 1.0) },
            { EnergyEngine.arrivalSoc(68.0, 70.0, Double.POSITIVE_INFINITY) },
        ).forEach { operation ->
            try { operation(); fail("Invalid input accepted") }
            catch (_: IllegalArgumentException) { }
        }
    }
}
