package com.monocucuy.solucion.scan

import android.app.KeyguardManager
import android.content.Context
import android.os.Build
import android.provider.Settings
import com.monocucuy.solucion.domain.*
import java.text.SimpleDateFormat
import java.util.Locale
import java.util.concurrent.TimeUnit

class SystemChecker(private val ctx: Context) {

    fun check(): List<Finding> {
        val out = mutableListOf<Finding>()
        val sys = Category.SYSTEM

        // Versión de Android
        if (Build.VERSION.SDK_INT < 30) {
            out += Finding(sys, Severity.HIGH, "Android desactualizado",
                "Android ${Build.VERSION.RELEASE} ya no recibe parches de seguridad.",
                "Considera cambiar de equipo o usar una ROM con soporte.")
        } else {
            out += Finding(sys, Severity.INFO, "Android", "Versión ${Build.VERSION.RELEASE} (API ${Build.VERSION.SDK_INT})")
        }

        // Parche de seguridad
        runCatching {
            val d = SimpleDateFormat("yyyy-MM-dd", Locale.US).parse(Build.VERSION.SECURITY_PATCH)!!
            val days = TimeUnit.MILLISECONDS.toDays(System.currentTimeMillis() - d.time)
            when {
                days > 365 -> out += Finding(sys, Severity.HIGH, "Parche de seguridad muy viejo",
                    "Último parche: ${Build.VERSION.SECURITY_PATCH} (hace $days días).", "Busca actualizaciones del sistema.")
                days > 180 -> out += Finding(sys, Severity.MEDIUM, "Parche de seguridad atrasado",
                    "Último parche: ${Build.VERSION.SECURITY_PATCH} (hace $days días).", "Busca actualizaciones del sistema.")
                else -> out += Finding(sys, Severity.INFO, "Parche de seguridad", "Último parche: ${Build.VERSION.SECURITY_PATCH}")
            }
        }

        // Bloqueo de pantalla
        val km = ctx.getSystemService(Context.KEYGUARD_SERVICE) as KeyguardManager
        if (!km.isDeviceSecure) {
            out += Finding(sys, Severity.HIGH, "Sin bloqueo de pantalla",
                "Cualquiera con el celular en la mano accede a todo.", "Activa PIN, patrón o huella en Ajustes.")
        }

        // Depuración USB
        val adb = Settings.Global.getInt(ctx.contentResolver, Settings.Global.ADB_ENABLED, 0) == 1
        if (adb) {
            out += Finding(sys, Severity.LOW, "Depuración USB activa",
                "Facilita que un equipo conectado acceda al celular.", "Desactívala si no desarrollas apps.")
        }
        return out
    }
}
