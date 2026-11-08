package com.ribhlab.rivomx

import java.util.Locale
import kotlin.math.sqrt

enum class MeasureMode(val label: String, val points: Int) {
    DISTANCE("Distance", 2), RECTANGLE("Length + Width", 4)
}
enum class UnitOfLength(val label: String, val factor: Double) {
    MM("mm", 1000.0), CM("cm", 100.0), M("m", 1.0), IN("in", 39.3700787);
    fun format(meters: Double?): String =
        if (meters == null) "—"
        else String.format(Locale.US, if (this == M) "%.3f %s" else "%.1f %s", meters * factor, label)
}
data class Point3(val x: Double, val y: Double, val z: Double)
data class Projected(val x: Float, val y: Float)
data class Readout(val length: Double? = null, val width: Double? = null, val hits: Int = 0, val source: String = "")
data class SavedMeasurement(val id: Long, val length: Double, val width: Double?, val source: String)
object MeasureMath {
    fun distance(a: Point3, b: Point3): Double = sqrt(
        (a.x - b.x) * (a.x - b.x) + (a.y - b.y) * (a.y - b.y) + (a.z - b.z) * (a.z - b.z)
    )
    fun area(a: Double?, b: Double?): Double? = if (a == null || b == null) null else a * b
}
