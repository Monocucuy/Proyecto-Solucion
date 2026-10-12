package com.monocucuy.solucion.domain

enum class Severity(val penalty: Int) { INFO(0), LOW(3), MEDIUM(8), HIGH(20) }

enum class Category(val label: String) {
    SECURITY("Seguridad"), HARDWARE("Hardware"), SYSTEM("Sistema")
}

data class Finding(
    val category: Category,
    val severity: Severity,
    val title: String,
    val detail: String,
    val action: String? = null,
    /** Paquete de la app que originó el hallazgo; null si no es de una app puntual. */
    val pkg: String? = null
)

data class ScanReport(
    val findings: List<Finding>,
    val score: Int,
    val appsScanned: Int,
    val categoryScores: Map<Category, Int> = emptyMap(),
    val timestamp: Long = System.currentTimeMillis()
) {
    companion object {
        fun build(findings: List<Finding>, appsScanned: Int): ScanReport {
            fun scoreOf(list: List<Finding>) = (100 - list.sumOf { it.severity.penalty }).coerceIn(0, 100)
            val byCategory = Category.values().associateWith { c -> scoreOf(findings.filter { it.category == c }) }
            return ScanReport(findings.sortedByDescending { it.severity }, scoreOf(findings), appsScanned, byCategory)
        }
    }
}

enum class Verdict { CLEAN, SUSPICIOUS, MALICIOUS, UNKNOWN }

data class Rep(
    val verdict: Verdict,
    val malicious: Int = 0,
    val suspicious: Int = 0,
    /**
     * "key" = clave de VirusTotal inválida, "token" = el servidor propio rechazó el token,
     * "limit" = límite de tasa, "net" = sin red, "pending" = el servidor aún no terminó de consultar,
     * "unavailable" = el servidor no pudo resolverlo (proveedores caídos / cola llena).
     */
    val error: String? = null
)

fun verdictOf(malicious: Int, suspicious: Int): Verdict = when {
    malicious >= 3 -> Verdict.MALICIOUS
    malicious + suspicious >= 1 -> Verdict.SUSPICIOUS
    else -> Verdict.CLEAN
}
