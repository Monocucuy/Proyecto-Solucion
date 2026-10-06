package com.monocucuy.solucion.data.repo

import com.monocucuy.solucion.domain.Rep
import com.monocucuy.solucion.domain.Verdict

/** Origen de reputación por hash. Nunca lanza por problemas de red/HTTP: devuelve UNKNOWN con `error`. */
interface ReputationSource {
    suspend fun lookupAll(
        hashes: List<String>,
        onProgress: (resolved: Int, total: Int) -> Unit
    ): Map<String, Rep>
}

/** Modo anterior: la app consulta VirusTotal directo con la clave del usuario. */
class DirectSource(
    private val repo: ReputationRepository,
    private val apiKey: String
) : ReputationSource {
    override suspend fun lookupAll(
        hashes: List<String>,
        onProgress: (resolved: Int, total: Int) -> Unit
    ): Map<String, Rep> {
        val unique = hashes.distinct()
        val out = LinkedHashMap<String, Rep>()
        for ((i, h) in unique.withIndex()) {
            val rep = repo.lookup(h, apiKey)
            out[h] = rep
            onProgress(i + 1, unique.size)
            if (rep.error == "key") {
                // Clave rechazada: no tiene sentido seguir golpeando a VirusTotal app por app.
                unique.drop(i + 1).forEach { out[it] = Rep(Verdict.UNKNOWN, error = "key") }
                break
            }
        }
        return out
    }
}
