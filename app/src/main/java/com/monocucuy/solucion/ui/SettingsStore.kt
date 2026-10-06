package com.monocucuy.solucion.ui

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

/** La clave de VirusTotal vive cifrada en el dispositivo, nunca en el repo. */
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
}
