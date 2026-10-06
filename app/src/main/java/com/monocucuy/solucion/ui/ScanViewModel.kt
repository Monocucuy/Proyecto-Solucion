package com.monocucuy.solucion.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.monocucuy.solucion.App
import com.monocucuy.solucion.domain.ScanReport
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

    var apiKey: String
        get() = c.settings.vtKey
        set(v) { c.settings.vtKey = v }

    fun startScan() {
        if (job?.isActive == true) return
        job = viewModelScope.launch {
            try {
                val all = mutableListOf<com.monocucuy.solucion.domain.Finding>()

                _state.value = UiState.Scanning("Hardware", 0, 0, "")
                all += c.hardware.check()

                _state.value = UiState.Scanning("Sistema", 0, 0, "")
                all += c.system.check()

                val res = c.appScanner.scan(apiKey.ifBlank { null }) { cur, tot, label ->
                    _state.value = UiState.Scanning("Apps", cur, tot, label)
                }
                all += res.findings

                _state.value = UiState.Done(ScanReport.build(all, res.scanned))
            } catch (e: CancellationException) {
                _state.value = UiState.Idle
                throw e
            } catch (e: Exception) {
                _state.value = UiState.Failed(e.message ?: "Error desconocido")
            }
        }
    }

    fun cancel() { job?.cancel() }
    fun reset() { _state.value = UiState.Idle }
}
