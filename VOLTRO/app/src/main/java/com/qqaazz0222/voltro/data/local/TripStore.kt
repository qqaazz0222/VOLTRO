package com.qqaazz0222.voltro.data.local

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import com.qqaazz0222.voltro.domain.model.TripRecord
import org.json.JSONObject

/** Device-only history. Coordinates are deliberately not persisted. */
class TripStore(context: Context) : SQLiteOpenHelper(context, "voltro.db", null, 1) {
    override fun onCreate(db: SQLiteDatabase) {
        db.execSQL("CREATE TABLE trips (id TEXT PRIMARY KEY, ended_at INTEGER NOT NULL, data TEXT NOT NULL)")
    }
    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) = Unit
    fun save(record: TripRecord) {
        val values = ContentValues().apply {
            put("id", record.id); put("ended_at", record.endedAt); put("data", record.json().toString())
        }
        val db = writableDatabase
        db.beginTransaction()
        try {
            check(db.insertWithOnConflict("trips", null, values, SQLiteDatabase.CONFLICT_REPLACE) != -1L) { "Trip insert failed" }
            db.execSQL("DELETE FROM trips WHERE id NOT IN (SELECT id FROM trips ORDER BY ended_at DESC LIMIT 50)")
            db.setTransactionSuccessful()
        } finally { db.endTransaction() }
    }
    fun recent(): List<TripRecord> = readableDatabase.query("trips", arrayOf("data"), null, null, null, null,
        "ended_at DESC", "50").use { cursor ->
        buildList { while (cursor.moveToNext()) add(JSONObject(cursor.getString(0)).record()) }
    }
    fun clear() { writableDatabase.delete("trips", null, null) }
}

fun TripRecord.json() = JSONObject().put("id", id).put("destination", destination).put("routeLabel", routeLabel)
    .put("startedAt", startedAt).put("endedAt", endedAt).put("distanceKm", distanceKm).put("durationMinutes", durationMinutes)
    .put("estimatedEnergyKwh", estimatedEnergyKwh).put("simulatedEnergyKwh", simulatedEnergyKwh)
    .put("initialSoc", initialSoc).put("finalSoc", finalSoc).put("remote", remote).put("synced", synced).put("routeSource", routeSource)
    .put("initialDurationMinutes", initialDurationMinutes ?: JSONObject.NULL).put("vehicleSource", vehicleSource)

private fun JSONObject.record() = TripRecord(getString("id"), getString("destination"), getString("routeLabel"),
    getLong("startedAt"), getLong("endedAt"), getDouble("distanceKm"), getDouble("durationMinutes"),
    getDouble("estimatedEnergyKwh"), getDouble("simulatedEnergyKwh"), getDouble("initialSoc"), getDouble("finalSoc"),
    optBoolean("remote"), optBoolean("synced"), optString("routeSource", "MOCK"), if (isNull("initialDurationMinutes")) null else getDouble("initialDurationMinutes"),
    optString("vehicleSource", "UNKNOWN"))
