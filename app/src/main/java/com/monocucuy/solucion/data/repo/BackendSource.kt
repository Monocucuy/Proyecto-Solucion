package com.monocucuy.solucion.data.repo

import com.monocucuy.solucion.data.local.HashCacheEntity
import com.monocucuy.solucion.data.local.HashDao
import com.monocucuy.solucion.data.remote.BackendApi
import com.monocucuy.solucion.data.remote.BackendResult
import com.monocucuy.solucion.data.remote.BatchRequest
import com.monocucuy.solucion.domain.Rep
import com.monocucuy.solucion.domain.Verdict
import kotlinx.coroutines.delay
import kotlinx.serialization.SerializationException
import java.io.IOException

/**
 * Consulta el backend propio en lote y sondea hasta que no queden pendientes o se agote [maxWaitMs].
 * El servidor sigue resolviendo la cola aunque la app deje de esperar, así que el siguiente escaneo
 * encuentra lo restante ya cacheado.
 */
class BackendSource(
    private val api: BackendApi,
    private val dao: HashDao,
    private val pollMs: Long = 4_000,
    private val maxWaitMs: Long = 120_000,
    private val clock: () -> Long = System::currentTimeMillis
) : ReputationSource {

    private val ttlMs = 7L * 24 * 60 * 60 * 1000
    private val maxBatch = 100 // MAX_BATCH del servidor

    override suspend fun lookupAll(
        hashes: List<String>,
        onProgress: (resolved: Int, total: Int) -> Unit
    ): Map<String, Rep> {
        val unique = hashes.distinct()
        val out = LinkedHashMap<String, Rep>()
        val start = clock()

        var pending = ArrayList<String>()
        for (h in unique) {
            val c = dao.get(h)
            if (c != null && start - c.checkedAt < ttlMs) out[h] = c.toRep() else pending += h
        }
        onProgress(out.size, unique.size)

        val deadline = start + maxWaitMs
        while (pending.isNotEmpty()) {
            val stillPending = ArrayList<String>()
            for (chunk in pending.chunked(maxBatch)) {
                val failure = try {
                    val resp = api.batch(BatchRequest(chunk))
                    val body = resp.body()
                    when {
                        resp.code() == 401 || resp.code() == 403 -> "token"
                        resp.code() == 429 -> "limit"
                        !resp.isSuccessful || body == null -> "unavailable"
                        else -> {
                            for (h in chunk) {
                                val r = body.results[h]
                                when (r?.status) {
                                    "done" -> out[h] = store(h, r)
                                    "unavailable" -> out[h] = Rep(Verdict.UNKNOWN, error = "unavailable")
                                    else -> stillPending += h // "pending" o ausente
                                }
                            }
                            null
                        }
                    }
                } catch (e: IOException) {
                    "net"
                } catch (e: SerializationException) {
                    "unavailable"
                }
                if (failure != null) {
                    // Falla de transporte/autorización: abortar todo lo que falta, no reintentar en bucle.
                    (pending - out.keys).forEach { out[it] = Rep(Verdict.UNKNOWN, error = failure) }
                    onProgress(unique.size, unique.size)
                    return out
                }
            }
            pending = stillPending
            onProgress(unique.size - pending.size, unique.size)
            if (pending.isEmpty()) break
            if (clock() >= deadline) {
                pending.forEach { out[it] = Rep(Verdict.UNKNOWN, error = "pending") }
                break
            }
            delay(pollMs)
        }
        return out
    }

    private suspend fun store(h: String, r: BackendResult): Rep {
        dao.upsert(HashCacheEntity(h, r.found, r.malicious, r.suspicious, clock()))
        val verdict = runCatching { Verdict.valueOf(r.verdict ?: "") }.getOrDefault(Verdict.UNKNOWN)
        return Rep(verdict, r.malicious, r.suspicious)
    }
}
