package com.monocucuy.solucion.ui

import android.app.Application
import android.os.Build
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.monocucuy.solucion.App
import com.monocucuy.solucion.domain.Finding
import com.monocucuy.solucion.domain.ScanReport
import com.monocucuy.solucion.domain.Severity
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

sealed interface UiState {
    data object Idle : UiState
    data class Scanning(val stage: String, val current: Int, val total: Int, val label: String) : UiState
    data class Done(val report: ScanReport) : UiState
    data class Failed(val message: String) : UiState
}

class ScanViewModel(app: Application) : AndroidViewModel(app) {
    private val c = (app as App).container
    private val _state = MutableStateFlow<UiState>(UiState.Idle)
    val state: StateFlow<UiState> = _state
    private var job: Job? = null

    // Hallazgos sin filtrar del último escaneo; el reporte se arma desde aquí para poder ocultar confiables.
    private var lastFindings: List<Finding> = emptyList()
    private var lastApps = 0

    var apiKey: String
        get() = c.settings.vtKey
        set(v) { c.settings.vtKey = v }

    var backendUrl: String
        get() = c.settings.backendUrl
        set(v) { c.settings.backendUrl = v }

    var backendToken: String
        get() = c.settings.backendToken
        set(v) { c.settings.backendToken = v }

    fun startScan() {
        if (job?.isActive == true) return
        job = viewModelScope.launch {
            val t0 = System.currentTimeMillis()
            try {
                val mode = when {
                    c.settings.backendUrl.isNotBlank() -> "servidor propio"
                    c.settings.vtKey.isNotBlank() -> "VirusTotal directo"
                    else -> "solo heurísticas"
                }
                // Antes del escaneo: contexto del equipo y modo de reputación (sin claves ni nombres de apps).
                c.debug.log("Inicio · ${Build.MANUFACTURER} ${Build.MODEL} · Android ${Build.VERSION.RELEASE} " +
                    "(API ${Build.VERSION.SDK_INT}) · reputación: $mode · confiables: ${c.settings.trustedApps.size}")

                val all = mutableListOf<Finding>()
                var lap = System.currentTimeMillis()
                fun stageDone(name: String) {
                    val now = System.currentTimeMillis()
                    c.debug.log("$name: ${now - lap} ms")
                    lap = now
                }

                _state.value = UiState.Scanning("Hardware", 0, 0, "")
                all += c.hardware.check()
                stageDone("Hardware")

                _state.value = UiState.Scanning("Sistema", 0, 0, "")
                all += c.system.check()
                stageDone("Sistema")

                val res = c.appScanner.scan(c.reputationSource(), c.settings.trustedApps) { cur, tot, label ->
                    _state.value = UiState.Scanning("Apps", cur, tot, label)
                }
                stageDone("Apps (${res.scanned} revisadas)")
                all += res.findings

                lastFindings = all
                lastApps = res.scanned
                val report = ScanReport.build(visible(), res.scanned)
                // Después del escaneo: resumen de resultados y duración total.
                c.debug.log("Fin · ${System.currentTimeMillis() - t0} ms · puntaje ${report.score} · " +
                    "hallazgos ${report.findings.size} ${report.findings.groupingBy { it.severity }.eachCount()}")
                _state.value = UiState.Done(report)
            } catch (e: CancellationException) {
                c.debug.log("Cancelado tras ${System.currentTimeMillis() - t0} ms")
                _state.value = UiState.Idle
                throw e
            } catch (e: Exception) {
                c.debug.log("ERROR durante el escaneo", e)
                _state.value = UiState.Failed(e.message ?: "Error desconocido")
            }
        }
    }

    /** Marca una app como confiable: se ocultan sus hallazgos, pero una detección de malware (HIGH) siempre se muestra. */
    fun trust(pkg: String) {
        c.settings.trustedApps = c.settings.trustedApps + pkg
        c.debug.log("App marcada como confiable (total: ${c.settings.trustedApps.size})")
        _state.value = UiState.Done(ScanReport.build(visible(), lastApps))
    }

    private fun visible(): List<Finding> {
        val trusted = c.settings.trustedApps
        return lastFindings.filterNot { f ->
            val pkg = f.pkg
            pkg != null && pkg in trusted && f.severity != Severity.HIGH
        }
    }

    fun debugText(): String = c.debug.read().ifBlank { "(sin registros todavía)" }

    fun cancel() { job?.cancel() }
    fun reset() { _state.value = UiState.Idle }
}
