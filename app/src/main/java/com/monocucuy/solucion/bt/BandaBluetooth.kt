package com.monocucuy.solucion.bt

import android.Manifest
import android.annotation.SuppressLint
import android.bluetooth.BluetoothManager
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.content.ContextCompat
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.IOException
import java.util.UUID

/** Puntaje mínimo para seguir derecho en la banda; por debajo va a revisión humana. */
const val UMBRAL_REVISION = 80

/** 'R' = necesita revisión humana, 'A' = sigue derecho. Son las letras que entiende el ESP32 de la banda. */
fun letraParaBanda(score: Int): Char = if (score < UMBRAL_REVISION) 'R' else 'A'

/**
 * Manda una letra por Bluetooth clásico (SPP) al ESP32 de la banda transportadora.
 * El celular debe estar emparejado antes con "BANDA-ESP32" (PIN 1233) desde Ajustes de Android.
 * Abre y cierra la conexión en cada envío: una letra por escaneo.
 */
class BandaBluetooth(private val ctx: Context) {

    /** Android 12+ pide BLUETOOTH_CONNECT en tiempo de ejecución; antes alcanza con el permiso del manifiesto. */
    fun tienePermiso(): Boolean = Build.VERSION.SDK_INT < Build.VERSION_CODES.S ||
        ContextCompat.checkSelfPermission(ctx, Manifest.permission.BLUETOOTH_CONNECT) == PackageManager.PERMISSION_GRANTED

    /** Devuelve null si la letra salió bien, o el motivo del fallo en español. */
    @SuppressLint("MissingPermission") // se comprueba arriba con tienePermiso()
    suspend fun enviar(letra: Char): String? = withContext(Dispatchers.IO) {
        if (!tienePermiso()) return@withContext "falta el permiso de Bluetooth"
        val adapter = ctx.getSystemService(BluetoothManager::class.java)?.adapter
            ?: return@withContext "este celular no tiene Bluetooth"
        if (!adapter.isEnabled) return@withContext "Bluetooth apagado"
        try {
            val banda = adapter.bondedDevices.firstOrNull { it.name == NOMBRE }
                ?: return@withContext "empareja primero $NOMBRE (PIN 1233) en Ajustes de Android"
            adapter.cancelDiscovery()
            banda.createRfcommSocketToServiceRecord(SPP).use { socket ->
                socket.connect()
                socket.outputStream.write(letra.code)
                socket.outputStream.flush()
                Thread.sleep(300) // deja que la letra salga antes de cerrar
            }
            null
        } catch (e: IOException) {
            "no se pudo conectar con la banda (${e.message ?: "sin detalle"})"
        } catch (e: SecurityException) {
            "Android negó el permiso de Bluetooth"
        }
    }

    companion object {
        const val NOMBRE = "BANDA-ESP32"
        private val SPP: UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")
    }
}
