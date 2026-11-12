package com.qqaazz0222.voltro.data.road

import com.qqaazz0222.voltro.domain.model.*
import com.qqaazz0222.voltro.domain.repository.RouteRepository
import com.qqaazz0222.voltro.domain.usecase.*
import kotlinx.coroutines.*
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.time.Instant
import java.util.UUID

const val ROAD_USER_AGENT = "VOLTRO/1.1.0 (+https://github.com/qqaazz0222/VOLTRO)"

class OsrmRouteRepository(private val origin: GeoPoint, private val baseUrl: String) : RouteRepository {
    private val gate = Mutex()
    private var previousRequest = 0L
    private val cache = mutableMapOf<GeoPoint, Pair<Long, JSONObject>>()

    override suspend fun compare(destination: Destination, vehicle: VehicleEnergyState, preferences: Preferences): RouteComparison =
        withContext(Dispatchers.IO) {
            val response = gate.withLock {
                val cached = cache[destination.point]
                if (cached != null && System.currentTimeMillis() - cached.first < 300000) cached.second
                else {
                    // The public routing service permits at most one request per second.
                    delay((1100 - (android.os.SystemClock.elapsedRealtime() - previousRequest)).coerceAtLeast(0))
                    previousRequest = android.os.SystemClock.elapsedRealtime()
                    val url = "$baseUrl/route/v1/driving/${origin.longitude},${origin.latitude};${destination.point.longitude},${destination.point.latitude}" +
                        "?alternatives=2&overview=full&geometries=geojson&annotations=distance,duration&steps=false"
                    val connection = URL(url).openConnection() as HttpURLConnection
                    val json = try {
                        require(connection.url.protocol == "https")
                        connection.connectTimeout = 10000; connection.readTimeout = 20000
                        connection.setRequestProperty("User-Agent", ROAD_USER_AGENT)
                        connection.setRequestProperty("Accept", "application/json")
                        require(connection.responseCode == 200) { "도로 경로 서비스가 응답하지 않습니다." }
                        val bytes = connection.inputStream.use { readBounded(it, 6_000_000) }
                        JSONObject(String(bytes, Charsets.UTF_8))
                    } finally { connection.disconnect() }
                    // Validate before caching. Failed/invalid responses never replace a valid result.
                    decode(json, destination, vehicle)
                    cache[destination.point] = System.currentTimeMillis() to json
                    json
                }
            }
            val routes = decode(response, destination, vehicle)
            RouteComparison(UUID.randomUUID().toString(), destination, routes, RouteRecommendation.recommend(routes, preferences),
                "OSRM · OpenStreetMap", Instant.now().toString())
        }

    private fun decode(json: JSONObject, destination: Destination, vehicle: VehicleEnergyState): List<RouteCandidate> {
        require(json.getString("code") == "Ok") { "이 목적지까지 연결되는 도로 경로가 없습니다." }
        val waypoints = json.getJSONArray("waypoints")
        require(waypoints.length() == 2 && (0..1).all { waypoints.getJSONObject(it).getDouble("distance") in 0.0..1000.0 })
        val array = json.getJSONArray("routes")
        require(array.length() in 1..3)
        val raw = (0 until array.length()).map { i ->
            val route = array.getJSONObject(i)
            val geometry = route.getJSONObject("geometry")
            require(geometry.getString("type") == "LineString")
            val coordinates = geometry.getJSONArray("coordinates")
            require(coordinates.length() in 2..100000)
            val points = (0 until coordinates.length()).map { c -> coordinates.getJSONArray(c).let { GeoPoint(it.getDouble(1), it.getDouble(0)) } }
            require(points.first().distanceTo(origin) <= 1000)
            val legs = route.getJSONArray("legs"); require(legs.length() == 1)
            val annotations = legs.getJSONObject(0).getJSONObject("annotation")
            fun values(name: String): List<Double> = annotations.getJSONArray(name).let { a ->
                require(a.length() == coordinates.length() - 1)
                (0 until a.length()).map { a.getDouble(it) }
            }
            RoadGeometry(route.getDouble("distance"), route.getDouble("duration"), points, values("distance"), values("duration"))
        }
        return RoadRouteMapper.candidates(raw, destination, vehicle)
    }
}
