package com.monocucuy.solucion.data.remote

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import retrofit2.Response
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.Path

interface VirusTotalApi {
    @GET("files/{hash}")
    suspend fun fileReport(
        @Path("hash") sha256: String,
        @Header("x-apikey") key: String
    ): Response<VtResponse>
}

@Serializable data class VtResponse(val data: VtData)
@Serializable data class VtData(val attributes: VtAttrs)
@Serializable data class VtAttrs(
    @SerialName("last_analysis_stats") val stats: VtStats = VtStats()
)
@Serializable data class VtStats(
    val malicious: Int = 0,
    val suspicious: Int = 0,
    val undetected: Int = 0,
    val harmless: Int = 0
)
