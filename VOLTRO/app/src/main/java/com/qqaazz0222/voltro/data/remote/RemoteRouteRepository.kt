package com.qqaazz0222.voltro.data.remote

import com.qqaazz0222.voltro.domain.model.*
import com.qqaazz0222.voltro.domain.repository.RouteRepository
import com.qqaazz0222.voltro.data.mock.point
import org.json.JSONObject

class RemoteRouteRepository(private val client: BackendClient, private val origin: GeoPoint) : RouteRepository {
    override suspend fun compare(destination: Destination, vehicle: VehicleEnergyState, preferences: Preferences): RouteComparison {
        val body = JSONObject().put("origin", origin.json()).put("destination", destination.point.json())
            .put("vehicle", JSONObject().put("soc_percent", vehicle.socPercent)
                .put("efficiency_km_per_kwh", vehicle.efficiencyKmPerKwh).put("usable_capacity_kwh", vehicle.usableBatteryCapacityKwh))
            .put("preferences", preferences.json())
        val response = client.request("/api/v1/routes/compare", body)
        require(response.getString("source") == "MOCK") { "지원하지 않는 경로 데이터입니다." }
        val array = response.getJSONArray("routes")
        val routes = (0 until array.length()).map { array.getJSONObject(it).let { r ->
            val nodes = r.getJSONArray("nodes")
            RouteCandidate(r.getString("route_id"), RouteType.valueOf(r.getString("route_type")), r.getString("label"),
                r.getString("road_name"), r.getDouble("distance_km"), r.getDouble("eta_minutes"), r.getDouble("energy_kwh"),
                r.getDouble("arrival_soc_percent"), r.getDouble("confidence"),
                (0 until nodes.length()).map { nodes.getJSONObject(it).let { n -> RouteNode(n.getString("node_id"), n.point(), n.getDouble("distance_km")) } })
        } }
        require(routes.size >= 2 && routes.map { it.id }.distinct().size == routes.size)
        require(routes.all { it.nodes.last().point.distanceTo(destination.point) < 100 })
        return RouteComparison(response.getString("trip_id"), destination, routes,
            response.optString("recommended_route_id").takeIf { it.isNotBlank() && it != "null" },
            response.getString("provider"), response.getString("calculated_at"), remote = true)
    }
}

fun GeoPoint.json() = JSONObject().put("latitude", latitude).put("longitude", longitude)
fun Preferences.json() = JSONObject().put("min_arrival_soc_percent", minArrivalSoc)
    .put("max_extra_minutes", maxExtraMinutes).put("min_energy_saving_kwh", minSavingKwh)
