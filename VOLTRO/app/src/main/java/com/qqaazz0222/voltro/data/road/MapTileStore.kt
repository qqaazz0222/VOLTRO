package com.qqaazz0222.voltro.data.road

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.http.HttpResponseCache
import android.os.Handler
import android.os.Looper
import android.util.LruCache
import com.qqaazz0222.voltro.R
import java.io.File
import java.lang.ref.WeakReference
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.Executors
import com.qqaazz0222.voltro.presentation.RoadMapView

/** Only visible viewport tiles are requested. HTTP cache preserves expiry, ETag and conditional GET. */
class MapTileStore private constructor(context: Context) {
    private val template = context.getString(R.string.map_tile_template)
    private val executor = Executors.newFixedThreadPool(2)
    private val main = Handler(Looper.getMainLooper())
    private val pending = mutableMapOf<String, MutableList<WeakReference<RoadMapView>>>()
    private val failedUntil = mutableMapOf<String, Long>()
    private data class Entry(val bitmap: Bitmap, val expiresAt: Long)
    private val memory = object : LruCache<String, Entry>(24 * 1024) {
        override fun sizeOf(key: String, value: Entry) = value.bitmap.byteCount / 1024
    }
    private val cacheReady = runCatching {
        HttpResponseCache.getInstalled() ?: HttpResponseCache.install(File(context.cacheDir, "road-map-http"), 64L * 1024 * 1024)
    }.isSuccess

    @Synchronized fun failed(key: String) = !cacheReady || (failedUntil[key] ?: 0) > System.currentTimeMillis()
    @Synchronized fun retry() { failedUntil.clear() }
    fun flush() { executor.execute { runCatching { HttpResponseCache.getInstalled()?.flush() } } }
    @Synchronized fun tile(key: String, view: RoadMapView): Bitmap? {
        memory.get(key)?.takeIf { it.expiresAt > System.currentTimeMillis() }?.let { return it.bitmap }
        if (failed(key)) return null
        pending[key]?.let { listeners ->
            listeners.removeAll { it.get()?.isAttachedToWindow != true }
            if (listeners.none { it.get() === view }) listeners.add(WeakReference(view))
            return null
        }
        pending[key] = mutableListOf(WeakReference(view))
        executor.execute { load(key) }
        return null
    }
    private fun load(key: String) {
        val visible = synchronized(this) { pending[key]?.any { it.get()?.wants(key) == true } == true }
        if (!visible) { synchronized(this) { pending.remove(key) }; return }
        val (z, x, y) = key.split("/")
        var connection: HttpURLConnection? = null
        try {
            val url = URL(template.replace("{z}", z).replace("{x}", x).replace("{y}", y))
            require(url.protocol == "https")
            connection = url.openConnection() as HttpURLConnection
            connection.connectTimeout = 8000; connection.readTimeout = 10000; connection.useCaches = true
            connection.setRequestProperty("User-Agent", ROAD_USER_AGENT)
            require(connection.responseCode == 200)
            val bitmap = connection.inputStream.use { input ->
                val bytes = readBounded(input, 1_000_000)
                BitmapFactory.decodeByteArray(bytes, 0, bytes.size) ?: error("Invalid map tile")
            }
            require(bitmap.width in 1..512 && bitmap.height in 1..512)
            val now = System.currentTimeMillis()
            val maxAge = Regex("max-age=(\\d+)").find(connection.getHeaderField("Cache-Control").orEmpty())
                ?.groupValues?.get(1)?.toLongOrNull()
            val age = maxOf(connection.getHeaderFieldLong("Age", 0) * 1000,
                (now - connection.getHeaderFieldDate("Date", now)).coerceAtLeast(0))
            val expires = if (maxAge != null) now + maxAge.coerceAtMost(31536000) * 1000 - age
                else connection.getHeaderFieldDate("Expires", now + 604800000)
            synchronized(this) { memory.put(key, Entry(bitmap, maxOf(now + 1000, expires))) }
        } catch (_: Exception) {
            synchronized(this) { failedUntil[key] = System.currentTimeMillis() + 60000 }
        } finally {
            connection?.disconnect()
            val listeners = synchronized(this) { pending.remove(key)?.mapNotNull { it.get() }.orEmpty() }
            main.post { listeners.filter { it.isAttachedToWindow }.forEach { it.invalidate() } }
        }
    }
    companion object {
        @Volatile private var instance: MapTileStore? = null
        fun get(context: Context): MapTileStore = instance ?: synchronized(this) {
            instance ?: MapTileStore(context.applicationContext).also { instance = it }
        }
        fun flushInstalled() { instance?.flush() }
    }
}

internal fun readBounded(input: java.io.InputStream, limit: Int): ByteArray {
    val output = java.io.ByteArrayOutputStream()
    val buffer = ByteArray(8192)
    while (true) {
        val read = input.read(buffer)
        if (read == -1) break
        require(output.size() + read <= limit) { "Network response exceeds limit" }
        output.write(buffer, 0, read)
    }
    return output.toByteArray()
}
