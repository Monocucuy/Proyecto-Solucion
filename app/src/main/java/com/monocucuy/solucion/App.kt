package com.monocucuy.solucion

import android.app.Application
import android.content.Context
import androidx.room.Room
import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import com.monocucuy.solucion.data.local.AppDb
import com.monocucuy.solucion.data.remote.VirusTotalApi
import com.monocucuy.solucion.data.repo.ReputationRepository
import com.monocucuy.solucion.scan.AppScanner
import com.monocucuy.solucion.scan.HardwareChecker
import com.monocucuy.solucion.scan.SystemChecker
import com.monocucuy.solucion.ui.SettingsStore
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import retrofit2.Retrofit

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
    private val api = Retrofit.Builder()
        .baseUrl("https://www.virustotal.com/api/v3/")
        .client(OkHttpClient.Builder().build())
        .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
        .build()
        .create(VirusTotalApi::class.java)

    private val repo = ReputationRepository(db.hashDao(), api)
    val appScanner = AppScanner(ctx, repo)
    val hardware = HardwareChecker(ctx)
    val system = SystemChecker(ctx)
}
