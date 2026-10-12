package com.monocucuy.solucion.scan

import android.content.Context
import android.content.pm.PackageManager
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.hardware.camera2.CameraAccessException
import android.hardware.camera2.CameraCharacteristics
import android.hardware.camera2.CameraManager
import android.nfc.NfcAdapter
import android.os.VibrationEffect
import android.os.Vibrator
import com.monocucuy.solucion.domain.Category
import com.monocucuy.solucion.domain.Finding
import com.monocucuy.solucion.domain.Severity
import kotlinx.coroutines.delay

/**
 * Pruebas activas con APIs públicas y sin root: sensores que responden, linterna, vibrador y componentes.
 * No incluye pruebas que requieren que el usuario toque o escuche (pantalla, altavoz, micrófono).
 */
class HardwareTests(private val ctx: Context) {
    private val hw = Category.HARDWARE

    suspend fun run(): List<Finding> = sensors() + actuators() + components()

    /** Registra todos los sensores de flujo continuo durante 2 s y mira cuáles entregan datos. */
    private suspend fun sensors(): List<Finding> {
        val sm = ctx.getSystemService(Context.SENSOR_SERVICE) as SensorManager
        val all = sm.getSensorList(Sensor.TYPE_ALL)
        val continuous = all.filter { it.reportingMode == Sensor.REPORTING_MODE_CONTINUOUS }
        val responded = HashSet<String>()
        val listener = object : SensorEventListener {
            override fun onSensorChanged(e: SensorEvent) { responded += key(e.sensor) }
            override fun onAccuracyChanged(s: Sensor?, accuracy: Int) = Unit
        }
        continuous.forEach { s -> runCatching { sm.registerListener(listener, s, SensorManager.SENSOR_DELAY_NORMAL) } }
        delay(2_000)
        sm.unregisterListener(listener)

        val silent = continuous.filter { key(it) !in responded }
        val out = mutableListOf<Finding>()
        out += Finding(hw, Severity.INFO, "Sensores",
            "${continuous.size - silent.size} de ${continuous.size} responden en 2 s · " +
                "${all.size - continuous.size} solo reportan cambios (no se prueban).")
        if (silent.isNotEmpty()) {
            out += Finding(hw, Severity.MEDIUM, "${silent.size} sensor(es) sin respuesta",
                silent.joinToString { it.name },
                "Puede ser falla de hardware o un bloqueo del sistema. Reinicia y vuelve a probar.")
        }
        return out
    }

    /** Linterna y vibrador: se activan brevemente para comprobar que responden. */
    private suspend fun actuators(): List<Finding> {
        val out = mutableListOf<Finding>()
        val cm = ctx.getSystemService(Context.CAMERA_SERVICE) as CameraManager
        val ids = runCatching { cm.cameraIdList.toList() }.getOrDefault(emptyList())
        fun characteristics(id: String) = runCatching { cm.getCameraCharacteristics(id) }.getOrNull()

        val facing = ids.mapNotNull { characteristics(it)?.get(CameraCharacteristics.LENS_FACING) }
        out += if (ids.isEmpty()) {
            Finding(hw, Severity.MEDIUM, "Sin cámaras", "El sistema no reporta ninguna cámara.")
        } else {
            Finding(hw, Severity.INFO, "Cámaras",
                "${facing.count { it == CameraCharacteristics.LENS_FACING_BACK }} trasera(s) · " +
                    "${facing.count { it == CameraCharacteristics.LENS_FACING_FRONT }} frontal(es).")
        }

        val flashId = ids.firstOrNull { characteristics(it)?.get(CameraCharacteristics.FLASH_INFO_AVAILABLE) == true }
        if (flashId == null) {
            out += Finding(hw, Severity.INFO, "Linterna", "No se detecta flash en las cámaras.")
        } else {
            // La linterna no necesita permiso de cámara.
            val ok = try {
                cm.setTorchMode(flashId, true)
                delay(400)
                cm.setTorchMode(flashId, false)
                true
            } catch (e: CameraAccessException) {
                false
            } catch (e: IllegalArgumentException) {
                false
            }
            out += if (ok) {
                Finding(hw, Severity.INFO, "Linterna", "Enciende y apaga correctamente.")
            } else {
                Finding(hw, Severity.MEDIUM, "Linterna no responde", "No se pudo activar el flash.",
                    "Puede estar en uso por otra app; cierra la cámara y reintenta.")
            }
        }

        val vib = ctx.getSystemService(Vibrator::class.java)
        if (vib == null || !vib.hasVibrator()) {
            out += Finding(hw, Severity.LOW, "Sin vibrador", "El sistema no reporta motor de vibración.")
        } else {
            vib.vibrate(VibrationEffect.createOneShot(200, VibrationEffect.DEFAULT_AMPLITUDE))
            delay(300)
            out += Finding(hw, Severity.INFO, "Vibración", "Motor presente; se activó 0,2 s.")
        }
        return out
    }

    /** Componentes presentes y estado de NFC. Wi-Fi, Bluetooth y GPS solo se revisan por presencia. */
    private fun components(): List<Finding> {
        val pm = ctx.packageManager
        val nfc = NfcAdapter.getDefaultAdapter(ctx)
        val nfcState = when {
            nfc == null -> "no"
            nfc.isEnabled -> "activo"
            else -> "apagado"
        }
        val features = listOf(
            "GPS" to PackageManager.FEATURE_LOCATION_GPS,
            "Wi-Fi" to PackageManager.FEATURE_WIFI,
            "Bluetooth" to PackageManager.FEATURE_BLUETOOTH,
            "Huella" to PackageManager.FEATURE_FINGERPRINT,
            "Micrófono" to PackageManager.FEATURE_MICROPHONE
        ).map { (name, feature) -> "$name ${if (pm.hasSystemFeature(feature)) "✔" else "✘"}" }
        return listOf(
            Finding(hw, Severity.INFO, "Componentes", (listOf("NFC $nfcState") + features).joinToString(" · "))
        )
    }

    private fun key(s: Sensor) = "${s.type}:${s.name}"
}
