package com.qqaazz0222.voltro.data.local

import android.content.Context
import android.util.AtomicFile
import com.qqaazz0222.voltro.domain.model.*
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

/** One private, expiring replay checkpoint. Kept out of OS backups; removed on cancel/completion. */
data class DrivingSession(
    val vehicle: VehicleEnergyState, val preferences: Preferences,
    val comparison: RouteComparison, val driving: DrivingState,
    val notified: Set<String>, val processedJunctions: Set<String>, val failRouteChange: Boolean,
)

class DrivingSessionStore(context: Context) {
    private val file = AtomicFile(File(context.noBackupFilesDir, "replay-session.json"))
    fun exists() = file.baseFile.exists() || File(file.baseFile.path + ".bak").exists()
    fun clear() = file.delete()
    fun save(session: DrivingSession) {
        val bytes = session.toJson().toString().toByteArray(Charsets.UTF_8)
        require(bytes.size <= MAX_BYTES) { "Replay checkpoint is too large" }
        val output = file.startWrite()
        try { output.write(bytes); file.finishWrite(output) }
        catch (failure: Exception) { file.failWrite(output); throw failure }
    }
    fun read(): DrivingSession? {
        if (!exists()) return null
        val json = file.openRead().use { input ->
            val bytes = input.readBytesLimited()
            JSONObject(String(bytes, Charsets.UTF_8))
        }
        require(json.getInt("version") == 1)
        val age = System.currentTimeMillis() - json.getLong("savedAt")
        require(age in -60_000L..86_400_000L) { "Replay checkpoint expired" }
        return json.session()
    }
    private fun java.io.InputStream.readBytesLimited(): ByteArray {
        val buffer = java.io.ByteArrayOutputStream()
        val chunk = ByteArray(8192)
        while (true) {
            val count = read(chunk)
            if (count == -1) break
            require(buffer.size() + count <= MAX_BYTES)
            buffer.write(chunk, 0, count)
        }
        return buffer.toByteArray()
    }
    companion object { private const val MAX_BYTES = 8 * 1024 * 1024 }
}

private fun GeoPoint.pointJson() = JSONArray().put(latitude).put(longitude)
private fun JSONArray.point() = GeoPoint(getDouble(0), getDouble(1))
private fun RouteCandidate.routeJson() = JSONObject().put("id", id).put("type", type.name).put("label", label)
    .put("road", roadName).put("distance", distanceKm).put("minutes", durationMinutes).put("energy", energyKwh)
    .put("soc", arrivalSoc).put("confidence", confidence).put("source", source.name)
    .put("nodes", JSONArray(nodes.map { n -> JSONArray().put(n.id).put(n.point.latitude).put(n.point.longitude)
        .put(n.distanceKm).put(n.elapsedMinutes ?: JSONObject.NULL) }))
private fun JSONObject.route() = RouteCandidate(getString("id"), RouteType.valueOf(getString("type")),
    getString("label"), getString("road"), getDouble("distance"), getDouble("minutes"), getDouble("energy"),
    getDouble("soc"), getDouble("confidence"), getJSONArray("nodes").let { nodes ->
        (0 until nodes.length()).map { i -> nodes.getJSONArray(i).let { n ->
            RouteNode(n.getString(0), GeoPoint(n.getDouble(1), n.getDouble(2)), n.getDouble(3),
                if (n.isNull(4)) null else n.getDouble(4))
        } }
    }, RouteSource.valueOf(getString("source")))
private fun JSONArray.strings() = (0 until length()).map { getString(it) }.toSet()

private fun DrivingSession.toJson(): JSONObject {
    val d = driving; val c = comparison; val v = vehicle
    return JSONObject().put("version", 1).put("savedAt", System.currentTimeMillis())
        .put("vehicle", JSONObject().put("soc", v.socPercent).put("efficiency", v.efficiencyKmPerKwh)
            .put("capacity", v.usableBatteryCapacityKwh).put("timestamp", v.timestamp).put("source", v.source.name)
            .put("efficiencySource", v.efficiencySource.name).put("capacitySource", v.capacitySource.name))
        .put("preferences", JSONArray().put(preferences.minArrivalSoc).put(preferences.maxExtraMinutes).put(preferences.minSavingKwh))
        .put("comparison", JSONObject().put("tripId", c.tripId).put("provider", c.provider).put("at", c.calculatedAt)
            .put("remote", c.remote).put("recommended", c.recommendedId ?: JSONObject.NULL)
            .put("destination", JSONObject().put("id", c.destination.id).put("name", c.destination.name)
                .put("description", c.destination.description).put("point", c.destination.point.pointJson()))
            .put("routes", JSONArray(c.routes.map { it.routeJson() })))
        .put("driving", JSONObject().put("active", d.activeRoute.id).put("initial", d.initialRoute.id)
            .put("startedAt", d.startedAt).put("distance", d.distanceKm).put("minutes", d.elapsedMinutes)
            .put("energy", d.consumedKwh).put("speed", d.speed).put("changed", d.routeChanged)
            .put("advice", d.advice?.let { a -> JSONObject().put("id", a.id).put("meters", a.distanceMeters)
                .put("alternative", a.alternative.id).put("saving", a.savingKwh).put("extra", a.additionalMinutes)
                .put("soc", a.arrivalSoc) } ?: JSONObject.NULL))
        .put("notified", JSONArray(notified.toList())).put("processed", JSONArray(processedJunctions.toList()))
        .put("failChange", failRouteChange)
}
private fun JSONObject.session(): DrivingSession {
    val v = getJSONObject("vehicle")
    val vehicle = VehicleEnergyState(v.getDouble("soc"), v.getDouble("efficiency"), v.getDouble("capacity"),
        timestamp = v.getLong("timestamp"), source = DataSource.valueOf(v.getString("source")),
        efficiencySource = DataSource.valueOf(v.getString("efficiencySource")), capacitySource = DataSource.valueOf(v.getString("capacitySource")))
    val p = getJSONArray("preferences")
    val preferences = Preferences(p.getDouble(0), p.getDouble(1), p.getDouble(2))
    val c = getJSONObject("comparison"); val target = c.getJSONObject("destination")
    val destination = Destination(target.getString("id"), target.getString("name"), target.getString("description"), target.getJSONArray("point").point())
    val routes = c.getJSONArray("routes").let { array -> (0 until array.length()).map { array.getJSONObject(it).route() } }
    require(routes.isNotEmpty() && routes.size <= 3 && routes.map { it.id }.distinct().size == routes.size)
    val comparison = RouteComparison(c.getString("tripId"), destination, routes,
        if (c.isNull("recommended")) null else c.getString("recommended"), c.getString("provider"), c.getString("at"), c.getBoolean("remote"))
    val d = getJSONObject("driving"); val active = routes.first { it.id == d.getString("active") }
    val initial = routes.first { it.id == d.getString("initial") }
    val distance = d.getDouble("distance"); val minutes = d.getDouble("minutes"); val energy = d.getDouble("energy")
    require(distance.isFinite() && distance in 0.0..active.distanceKm)
    require(minutes.isFinite() && minutes >= 0 && energy.isFinite() && energy >= 0)
    require(d.getInt("speed") in listOf(1, 4, 12))
    val advice = d.optJSONObject("advice")?.let { a -> JunctionAdvice(a.getString("id"), a.getDouble("meters"),
        routes.first { it.id == a.getString("alternative") }, a.getDouble("saving"), a.getDouble("extra"), a.getDouble("soc")) }
    val driving = DrivingState(comparison.tripId, active, initial, startedAt = d.getLong("startedAt"),
        distanceKm = distance, elapsedMinutes = minutes, consumedKwh = energy, position = active.pointAt(distance),
        paused = true, speed = d.getInt("speed"), advice = advice, routeChanged = d.getBoolean("changed"))
    return DrivingSession(vehicle, preferences, comparison, driving, getJSONArray("notified").strings(),
        getJSONArray("processed").strings(), getBoolean("failChange"))
}
