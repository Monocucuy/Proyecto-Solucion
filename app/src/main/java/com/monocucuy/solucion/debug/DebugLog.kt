package com.monocucuy.solucion.debug

import android.content.Context
import android.util.Log
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * Registro local de depuración: fases del escaneo, duración, errores y crashes.
 * No guarda hashes ni nombres de apps. Vive solo en el dispositivo; sale únicamente si el usuario lo comparte.
 */
class DebugLog(ctx: Context) {
    private val file = File(ctx.filesDir, "debug.log")
    private val fmt = SimpleDateFormat("HH:mm:ss.SSS", Locale.US)

    @Synchronized
    fun log(msg: String, t: Throwable? = null) {
        val line = buildString {
            append(fmt.format(Date())).append(' ').append(msg).append('\n')
            t?.let { append(Log.getStackTraceString(it).trimEnd()).append('\n') }
        }
        Log.d(TAG, msg)
        runCatching {
            file.appendText(line)
            if (file.length() > MAX_BYTES) trim()
        }
    }

    /** Conserva la mitad final del archivo, desde la siguiente línea completa. */
    private fun trim() {
        val text = file.readText()
        file.writeText(text.substring(text.length / 2).substringAfter('\n'))
    }

    @Synchronized
    fun read(): String = runCatching { file.readText() }.getOrDefault("")

    companion object {
        const val TAG = "SolucionDebug"
        private const val MAX_BYTES = 200_000L
    }
}
