package com.monocucuy.solucion

import android.app.Application
import android.content.Context
import androidx.room.Room
import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import com.monocucuy.solucion.data.local.AppDb
import com.monocucuy.solucion.data.remote.BackendApi
import com.monocucuy.solucion.data.remote.VirusTotalApi
import com.monocucuy.solucion.data.repo.BackendSource
import com.monocucuy.solucion.data.repo.DirectSource
import com.monocucuy.solucion.data.repo.ReputationRepository
import com.monocucuy.solucion.data.repo.ReputationSource
import com.monocucuy.solucion.scan.AppScanner
import com.monocucuy.solucion.scan.HardwareChecker
import com.monocucuy.solucion.scan.SystemChecker
import com.monocucuy.solucion.ui.SettingsStore
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.HttpUrl.Companion.toHttpUrlOrNull
import okhttp3.OkHttpClient
import retrofit2.Retrofit
import java.util.concurrent.TimeUnit

class App : Application() {
    lateinit var container: AppContainer
    override fun onCreate() {
        super.onCreate()
        container = AppContainer(this)
    }
}

/** DI manual: suficiente para el MVP, sin Hilt. */
class AppContainer(ctx: Context) {
    val settings = SettingsStore(ctx)

    private val db = Room.databaseBuilder(ctx, AppDb::class.java, "solucion.db").build()
    private val json = Json { ignoreUnknownKeys = true }
    private val jsonConverter = json.asConverterFactory("application/json".toMediaType())

    private val vtApi = Retrofit.Builder()
        .baseUrl("https://www.virustotal.com/api/v3/")
        .client(OkHttpClient.Builder().build())
        .addConverterFactory(jsonConverter)
        .build()
        .create(VirusTotalApi::class.java)

    private val repo = ReputationRepository(db.hashDao(), vtApi)

    /** El token (si hay) viaja como Bearer; la URL puede cambiar en Ajustes, por eso no se cachea el cliente. */
    private fun backendApi(url: String, token: String): BackendApi {
        val base = url.trim().trimEnd('/') + "/"
        if (base.toHttpUrlOrNull() == null) throw IllegalArgumentException("La URL del servidor no es válida: $url")
        val client = OkHttpClient.Builder()
            .connectTimeout(10, TimeUnit.SECONDS)
            .readTimeout(20, TimeUnit.SECONDS)
            .addInterceptor { chain ->
                val req = if (token.isBlank()) chain.request()
                else chain.request().newBuilder().header("Authorization", "Bearer ${token.trim()}").build()
                chain.proceed(req)
            }
            .build()
        return Retrofit.Builder().baseUrl(base).client(client).addConverterFactory(jsonConverter).build()
            .create(BackendApi::class.java)
    }

    /**
     * Prioridad: servidor propio (si hay URL) > VirusTotal directo (si hay clave) > null (solo heurísticas locales).
     * Lanza IllegalArgumentException si la URL del servidor es inválida.
     */
    fun reputationSource(): ReputationSource? {
        val url = settings.backendUrl
        if (url.isNotBlank()) return BackendSource(backendApi(url, settings.backendToken), db.hashDao())
        val key = settings.vtKey
        return if (key.isNotBlank()) DirectSource(repo, key) else null
    }

    val appScanner = AppScanner(ctx)
    val hardware = HardwareChecker(ctx)
    val system = SystemChecker(ctx)
}
