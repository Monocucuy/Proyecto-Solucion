package com.monocucuy.solucion.data.repo

import com.monocucuy.solucion.data.local.HashCacheEntity
import com.monocucuy.solucion.data.local.HashDao
import com.monocucuy.solucion.data.remote.VirusTotalApi
import com.monocucuy.solucion.domain.Rep
import com.monocucuy.solucion.domain.Verdict
import com.monocucuy.solucion.domain.verdictOf
import kotlinx.coroutines.delay
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import java.io.IOException

/** Consulta reputación por hash. Solo hash: nunca se sube el APK. */
class ReputationRepository(
    private val dao: HashDao,
    private val api: VirusTotalApi
) {
    private val ttlMs = 7L * 24 * 60 * 60 * 1000
    private val minGapMs = 15_000L // clave gratuita ~4 consultas/min
    private val mutex = Mutex()
    private var lastCall = 0L

    suspend fun lookup(sha256: String, apiKey: String): Rep {
        val now = System.currentTimeMillis()
        dao.get(sha256)?.let { if (now - it.checkedAt < ttlMs) return it.toRep() }

        var attempts = 0
        while (true) {
            throttle()
            val resp = try {
                api.fileReport(sha256, apiKey)
            } catch (e: IOException) {
                return Rep(Verdict.UNKNOWN, error = "net")
            }
            when (resp.code()) {
                200 -> {
                    val s = resp.body()?.data?.attributes?.stats
                        ?: return Rep(Verdict.UNKNOWN)
                    dao.upsert(HashCacheEntity(sha256, true, s.malicious, s.suspicious, System.currentTimeMillis()))
                    return Rep(verdictOf(s.malicious, s.suspicious), s.malicious, s.suspicious)
                }
                // 404 = VirusTotal nunca vio este hash. NO significa "limpia".
                404 -> {
                    dao.upsert(HashCacheEntity(sha256, false, 0, 0, System.currentTimeMillis()))
                    return Rep(Verdict.UNKNOWN)
                }
                429 -> {
                    if (++attempts >= 2) return Rep(Verdict.UNKNOWN, error = "limit")
                    delay(30_000)
                }
                401, 403 -> return Rep(Verdict.UNKNOWN, error = "key")
                else -> return Rep(Verdict.UNKNOWN)
            }
        }
    }

    private suspend fun throttle() = mutex.withLock {
        val wait = minGapMs - (System.currentTimeMillis() - lastCall)
        if (wait > 0) delay(wait)
        lastCall = System.currentTimeMillis()
    }
}

fun HashCacheEntity.toRep() =
    if (!found) Rep(Verdict.UNKNOWN) else Rep(verdictOf(malicious, suspicious), malicious, suspicious)
