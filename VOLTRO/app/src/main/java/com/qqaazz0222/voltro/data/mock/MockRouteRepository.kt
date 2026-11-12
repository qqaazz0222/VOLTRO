package com.qqaazz0222.voltro.data.mock

import com.qqaazz0222.voltro.domain.model.*
import com.qqaazz0222.voltro.domain.repository.RouteRepository
import com.qqaazz0222.voltro.domain.usecase.*
import org.json.JSONObject
import java.util.Date
import java.util.UUID

class MockRouteRepository(private val scenario: JSONObject) : RouteRepository {
    val origin = scenario.getJSONObject("origin").point()
    val destinations: List<Destination> = scenario.getJSONArray("destinations").let { array ->
        (0 until array.length()).map { array.getJSONObject(it).let { d ->
            Destination(d.getString("id"), d.getString("name"), d.getString("description"), d.point())
        } }
    }

    override suspend fun compare(destination: Destination, vehicle: VehicleEnergyState, preferences: Preferences): RouteComparison {
        val targets = scenario.getJSONArray("destinations")
        val target = (0 until targets.length()).map { targets.getJSONObject(it) }.first { it.getString("id") == destination.id }
        val scale = target.getDouble("distance_scale")
        val templates = scenario.getJSONArray("routes")
        val routes = (0 until templates.length()).map { i ->
            val t = templates.getJSONObject(i)
            val type = RouteType.valueOf(t.getString("route_type"))
            val distance = t.getDouble("distance_km") * scale
            val common = scenario.getJSONArray("common_nodes")
            val nodes = (0 until common.length()).map { common.getJSONObject(it).let { n ->
                RouteNode(n.getString("node_id"), n.point(), n.getDouble("distance_km"))
            } }.toMutableList()
            val via = t.getJSONArray("via")
            for (j in 0 until via.length()) nodes.add(RouteNode("${type.name}_$j", via.getJSONObject(j).point(),
                35 + (distance - 35) * (j + 1) / 3))
            nodes.add(RouteNode(destination.id, destination.point, distance))
            val energy = EnergyEngine.predict(distance, vehicle.efficiencyKmPerKwh)
            RouteCandidate("${destination.id}_${type.name.lowercase()}", type, t.getString("label"), t.getString("road_name"),
                distance, t.getDouble("eta_minutes") * scale, energy,
                EnergyEngine.arrivalSoc(vehicle.socPercent, vehicle.usableBatteryCapacityKwh, energy), 0.9, nodes)
        }
        return RouteComparison(UUID.randomUUID().toString(), destination, routes, RouteRecommendation.recommend(routes, preferences),
            scenario.getString("provider"), Date().toString())
    }
}

fun JSONObject.point() = GeoPoint(getDouble("latitude"), getDouble("longitude"))
