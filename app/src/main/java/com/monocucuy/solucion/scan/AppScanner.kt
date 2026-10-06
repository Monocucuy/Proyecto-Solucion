package com.monocucuy.solucion.scan

import android.content.Context
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import android.os.Build
import com.monocucuy.solucion.data.repo.ReputationSource
import com.monocucuy.solucion.domain.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.security.MessageDigest

class AppScanner(private val ctx: Context) {

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
        source: ReputationSource?,
        onProgress: (current: Int, total: Int, label: String) -> Unit
    ): Result = withContext(Dispatchers.IO) {
        val pm = ctx.packageManager
        val apps = pm.getInstalledApplications(0)
            .filter { it.flags and ApplicationInfo.FLAG_SYSTEM == 0 && it.packageName != ctx.packageName }

        val findings = mutableListOf<Finding>()
        val labelsByHash = LinkedHashMap<String, MutableList<String>>()
        var unhashed = 0

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

            // Solo se calcula el hash; el APK nunca sale del dispositivo.
            if (source != null) {
                val sha = runCatching { sha256(info.sourceDir) }.getOrNull()
                if (sha == null) unhashed++ else labelsByHash.getOrPut(sha) { mutableListOf() } += label
            }
        }

        // --- Reputación por hash ---
        if (source == null) {
            findings += Finding(Category.SECURITY, Severity.INFO, "Sin servicio de reputación",
                "Solo se aplicaron heurísticas locales.",
                "En Ajustes configura tu servidor o pega una clave gratuita de VirusTotal.")
        } else {
            val reps = source.lookupAll(labelsByHash.keys.toList()) { done, total ->
                onProgress(done, total, "Consultando reputación…")
            }
            var unknownCount = unhashed
            val errors = mutableMapOf<String, Int>()
            for ((sha, labels) in labelsByHash) {
                val rep = reps[sha] ?: Rep(Verdict.UNKNOWN, error = "unavailable")
                rep.error?.let { errors.merge(it, labels.size, Int::plus) }
                for (label in labels) {
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
                        Verdict.UNKNOWN -> if (rep.error == null) unknownCount++
                        Verdict.CLEAN -> Unit
                    }
                }
            }
            errors["key"]?.let {
                findings += Finding(Category.SECURITY, Severity.INFO, "Clave de VirusTotal inválida",
                    "VirusTotal rechazó la clave.", "Revísala en Ajustes.")
            }
            errors["token"]?.let {
                findings += Finding(Category.SECURITY, Severity.INFO, "El servidor rechazó el token",
                    "No se pudo verificar la reputación de $it app(s).", "Revisa el token en Ajustes.")
            }
            errors["limit"]?.let {
                findings += Finding(Category.SECURITY, Severity.INFO, "Límite de consultas alcanzado",
                    "$it app(s) quedaron sin verificar.", "Vuelve a escanear más tarde; lo ya consultado queda en cache.")
            }
            errors["net"]?.let {
                findings += Finding(Category.SECURITY, Severity.INFO, "Sin conexión con el servicio de reputación",
                    "$it app(s) quedaron sin verificar.", "Revisa tu conexión y la URL del servidor en Ajustes.")
            }
            errors["pending"]?.let {
                findings += Finding(Category.SECURITY, Severity.INFO, "Consulta de reputación incompleta",
                    "El servidor sigue consultando $it app(s); lo ya resuelto quedó guardado.",
                    "Escanea de nuevo en unos minutos.")
            }
            errors["unavailable"]?.let {
                findings += Finding(Category.SECURITY, Severity.INFO, "Servicio de reputación no disponible",
                    "$it app(s) quedaron sin verificar.", "Intenta de nuevo más tarde.")
            }
            if (unknownCount > 0) {
                findings += Finding(Category.SECURITY, Severity.INFO, "$unknownCount app(s) sin datos",
                    "Los antivirus no conocen esos archivos. Sin datos no significa limpia.")
            }
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
