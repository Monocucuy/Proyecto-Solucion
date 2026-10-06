package com.monocucuy.solucion.data.remote

import kotlinx.serialization.Serializable
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST

/** Contrato en backend/README.md. Solo viajan hashes SHA-256: nunca archivos, rutas ni nombres de apps. */
interface BackendApi {
    @POST("v1/reputation/batch")
    suspend fun batch(@Body req: BatchRequest): Response<BatchResponse>
}

@Serializable data class BatchRequest(val hashes: List<String>)

@Serializable data class BatchResponse(
    val results: Map<String, BackendResult> = emptyMap(),
    val pending: Int = 0
)

/** status: "done" | "pending" | "unavailable". */
@Serializable data class BackendResult(
    val status: String,
    val verdict: String? = null,
    val found: Boolean = false,
    val malicious: Int = 0,
    val suspicious: Int = 0,
    val error: String? = null
)
