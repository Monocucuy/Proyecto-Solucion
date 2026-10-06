package com.monocucuy.solucion.scan

import android.content.Context
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import android.os.Build
import com.monocucuy.solucion.data.repo.ReputationRepository
import com.monocucuy.solucion.domain.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.security.MessageDigest

class AppScanner(private val ctx: Context, private val repo: ReputationRepository) {

    data class Result(val findings: List<Finding>, val scanned: Int)

    private val riskyPerms = setOf(
        "android.permission.SEND_SMS",
        "android.permission.READ_SMS",
        "android.permission.RECEIVE_SMS",
        "android.permission.BIND_ACCESSIBILITY_SERVICE",
        "android.permission.SYSTEM_ALERT_WINDOW",
        "android.permission.REQUEST_INSTALL_PACKAGES",
        "android.permission.BIND_DEVICE_ADMIN"
    )

    suspend fun scan(
        apiKey: String?,
        onProgress: (current: Int, total: Int, label: String) -> Unit
    ): Result = withContext(Dispatchers.IO) {
        val pm = ctx.packageManager
        val apps = pm.getInstalledApplications(0)
            .filter { it.flags and ApplicationInfo.FLAG_SYSTEM == 0 && it.packageName != ctx.packageName }

        val findings = mutableListOf<Finding>()
        var keyErrorReported = false
        var limitReported = false
        var unknownCount = 0

        apps.forEachIndexed { i, info ->
            val label = pm.getApplicationLabel(info).toString()
            onProgress(i + 1, apps.size, label)

            // --- Heurísticas locales (funcionan sin internet) ---
            val perms = runCatching {
                pm.getPackageInfo(info.packageName, PackageManager.GET_PERMISSIONS).requestedPermissions
            }.getOrNull().orEmpty().filter { it in riskyPerms }

            if (perms.size >= 3) {
                findings += Finding(
                    Category.SECURITY, Severity.MEDIUM,
                    "$label pide permisos delicados",
                    "Combina ${perms.size} permisos de riesgo: ${perms.joinToString { it.substringAfterLast('.') }}.",
                    "Revisa si realmente necesitas esta app."
                )
            }

            val installer = if (Build.VERSION.SDK_INT >= 30) {
                runCatching { pm.getInstallSourceInfo(info.packageName).installingPackageName }.getOrNull()
            } else {
                @Suppress("DEPRECATION") pm.getInstallerPackageName(info.packageName)
            }
            if (installer != "com.android.vending") {
                findings += Finding(
                    Category.SECURITY, Severity.LOW,
                    "$label no viene de Google Play",
                    "Instalada desde: ${installer ?: "origen desconocido / APK manual"}.",
                    "Instala apps solo de fuentes que conozcas."
                )
            }

            // --- Reputación por hash (VirusTotal) ---
            if (!apiKey.isNullOrBlank()) {
                val sha = sha256(info.sourceDir)
                val rep = repo.lookup(sha, apiKey)
                when (rep.verdict) {
                    Verdict.MALICIOUS -> findings += Finding(
                        Category.SECURITY, Severity.HIGH,
                        "$label detectada como maliciosa",
                        "${rep.malicious} motores antivirus la marcan como maliciosa.",
                        "Desinstálala ahora."
                    )
                    Verdict.SUSPICIOUS -> findings += Finding(
                        Category.SECURITY, Severity.MEDIUM,
                        "$label es sospechosa",
                        "Marcada por ${rep.malicious + rep.suspicious} motor(es). Puede ser falso positivo.",
                        "Verifica el origen o desinstálala."
                    )
                    Verdict.UNKNOWN -> unknownCount++
                    Verdict.CLEAN -> Unit
                }
                if (rep.error == "key" && !keyErrorReported) {
                    keyErrorReported = true
                    findings += Finding(Category.SECURITY, Severity.INFO, "Clave de VirusTotal inválida",
                        "VirusTotal rechazó la clave.", "Revísala en Ajustes.")
                }
                if (rep.error == "limit" && !limitReported) {
                    limitReported = true
                    findings += Finding(Category.SECURITY, Severity.INFO, "Límite de VirusTotal alcanzado",
                        "Algunas apps quedaron sin verificar.", "Vuelve a escanear más tarde; lo ya consultado queda en cache.")
                }
            }
        }

        if (apiKey.isNullOrBlank()) {
            findings += Finding(Category.SECURITY, Severity.INFO, "Sin clave de VirusTotal",
                "Solo se aplicaron heurísticas locales.", "Pega tu clave gratuita en Ajustes.")
        } else if (unknownCount > 0) {
            findings += Finding(Category.SECURITY, Severity.INFO, "$unknownCount app(s) sin datos",
                "VirusTotal no conoce esos archivos. Sin datos no significa limpia.")
        }
        Result(findings, apps.size)
    }

    private fun sha256(path: String): String {
        val md = MessageDigest.getInstance("SHA-256")
        File(path).inputStream().use { s ->
            val buf = ByteArray(8192)
            while (true) {
                val n = s.read(buf)
                if (n < 0) break
                md.update(buf, 0, n)
            }
        }
        return md.digest().joinToString("") { "%02x".format(it) }
    }
}
