package com.monocucuy.solucion.ui

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

/** Clave de VirusTotal y token del servidor viven cifrados en el dispositivo, nunca en el repo. */
class SettingsStore(ctx: Context) {
    private val prefs = EncryptedSharedPreferences.create(
        ctx,
        "secure_prefs",
        MasterKey.Builder(ctx).setKeyScheme(MasterKey.KeyScheme.AES256_GCM).build(),
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )

    var vtKey: String
        get() = prefs.getString("vt_key", "") ?: ""
        set(v) = prefs.edit().putString("vt_key", v.trim()).apply()

    /** URL del backend propio (ej. https://reputacion.midominio.com). Vacío = consultar VirusTotal directo. */
    var backendUrl: String
        get() = prefs.getString("backend_url", "") ?: ""
        set(v) = prefs.edit().putString("backend_url", v.trim()).apply()

    var backendToken: String
        get() = prefs.getString("backend_token", "") ?: ""
        set(v) = prefs.edit().putString("backend_token", v.trim()).apply()

    /** Paquetes marcados como confiables desde el reporte. Se ocultan sus hallazgos, salvo detecciones de malware. */
    var trustedApps: Set<String>
        get() = prefs.getStringSet("trusted_apps", emptySet()) ?: emptySet()
        set(v) = prefs.edit().putStringSet("trusted_apps", v.toSet()).apply()
}
