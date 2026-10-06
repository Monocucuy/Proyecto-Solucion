package com.monocucuy.solucion.ui

import android.content.Intent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.monocucuy.solucion.domain.Finding
import com.monocucuy.solucion.domain.ScanReport
import com.monocucuy.solucion.domain.Severity
import java.text.DateFormat
import java.util.Date

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ScannerApp(vm: ScanViewModel = viewModel()) {
    val state by vm.state.collectAsStateWithLifecycle()
    var showSettings by remember { mutableStateOf(false) }

    MaterialTheme {
        Scaffold(
            topBar = {
                TopAppBar(
                    title = { Text("Solución Scanner") },
                    actions = { TextButton(onClick = { showSettings = true }) { Text("Ajustes") } }
                )
            }
        ) { pad ->
            Box(Modifier.padding(pad).fillMaxSize()) {
                when (val s = state) {
                    UiState.Idle -> Home(onScan = vm::startScan)
                    is UiState.Scanning -> Progress(s, onCancel = vm::cancel)
                    is UiState.Done -> Report(s.report, onRescan = vm::startScan)
                    is UiState.Failed -> Failed(s.message, onRetry = vm::reset)
                }
            }
        }
        if (showSettings) SettingsDialog(
            current = vm.apiKey,
            onSave = { vm.apiKey = it; showSettings = false },
            onDismiss = { showSettings = false }
        )
    }
}

@Composable
private fun Home(onScan: () -> Unit) = Column(
    Modifier.fillMaxSize().padding(24.dp),
    verticalArrangement = Arrangement.Center,
    horizontalAlignment = Alignment.CenterHorizontally
) {
    Text("¿Cómo está tu celular?", fontSize = 24.sp, fontWeight = FontWeight.Bold)
    Spacer(Modifier.height(8.dp))
    Text("Revisamos apps, hardware y configuración del sistema.")
    Spacer(Modifier.height(32.dp))
    Button(onClick = onScan, modifier = Modifier.fillMaxWidth().height(56.dp)) { Text("Escanear") }
}

@Composable
private fun Progress(s: UiState.Scanning, onCancel: () -> Unit) = Column(
    Modifier.fillMaxSize().padding(24.dp),
    verticalArrangement = Arrangement.Center,
    horizontalAlignment = Alignment.CenterHorizontally
) {
    Text("Escaneando: ${s.stage}", fontSize = 20.sp, fontWeight = FontWeight.SemiBold)
    Spacer(Modifier.height(16.dp))
    if (s.total > 0) {
        LinearProgressIndicator(progress = { s.current / s.total.toFloat() }, modifier = Modifier.fillMaxWidth())
        Spacer(Modifier.height(8.dp))
        Text("${s.current} / ${s.total} · ${s.label}")
        Spacer(Modifier.height(8.dp))
        Text("Con la clave gratuita de VirusTotal esto puede tardar varios minutos.", fontSize = 12.sp)
    } else {
        LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
    }
    Spacer(Modifier.height(24.dp))
    OutlinedButton(onClick = onCancel) { Text("Cancelar") }
}

@Composable
private fun Report(report: ScanReport, onRescan: () -> Unit) {
    val ctx = LocalContext.current
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        item {
            Column(Modifier.fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally) {
                Text("${report.score}", fontSize = 64.sp, fontWeight = FontWeight.Bold, color = scoreColor(report.score))
                Text("Puntaje de salud · ${report.appsScanned} apps revisadas")
                Text(DateFormat.getDateTimeInstance().format(Date(report.timestamp)), fontSize = 12.sp)
                Spacer(Modifier.height(8.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(onClick = onRescan) { Text("Escanear de nuevo") }
                    OutlinedButton(onClick = {
                        ctx.startActivity(Intent.createChooser(Intent(Intent.ACTION_SEND).apply {
                            type = "text/plain"
                            putExtra(Intent.EXTRA_TEXT, reportText(report))
                        }, "Compartir reporte"))
                    }) { Text("Compartir") }
                }
            }
        }
        items(report.findings) { FindingCard(it) }
    }
}

@Composable
private fun FindingCard(f: Finding) = Card(Modifier.fillMaxWidth()) {
    Column(Modifier.padding(12.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(f.severity.name, color = severityColor(f.severity), fontWeight = FontWeight.Bold, fontSize = 12.sp)
            Spacer(Modifier.width(8.dp))
            Text(f.category.label, fontSize = 12.sp)
        }
        Text(f.title, fontWeight = FontWeight.SemiBold)
        Text(f.detail, fontSize = 14.sp)
        f.action?.let { Text("→ $it", fontSize = 14.sp, fontWeight = FontWeight.Medium) }
    }
}

@Composable
private fun Failed(msg: String, onRetry: () -> Unit) = Column(
    Modifier.fillMaxSize().padding(24.dp),
    verticalArrangement = Arrangement.Center,
    horizontalAlignment = Alignment.CenterHorizontally
) {
    Text("Algo falló", fontSize = 20.sp, fontWeight = FontWeight.Bold)
    Text(msg)
    Spacer(Modifier.height(16.dp))
    Button(onClick = onRetry) { Text("Volver") }
}

@Composable
private fun SettingsDialog(current: String, onSave: (String) -> Unit, onDismiss: () -> Unit) {
    var key by remember { mutableStateOf(current) }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Clave de VirusTotal") },
        text = {
            Column {
                Text("Pega tu clave gratuita de virustotal.com. Se guarda cifrada en este dispositivo.", fontSize = 13.sp)
                Spacer(Modifier.height(8.dp))
                OutlinedTextField(value = key, onValueChange = { key = it }, singleLine = true, label = { Text("API key") })
            }
        },
        confirmButton = { TextButton(onClick = { onSave(key) }) { Text("Guardar") } },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancelar") } }
    )
}

private fun scoreColor(s: Int) = when {
    s >= 80 -> Color(0xFF2E7D32)
    s >= 50 -> Color(0xFFF9A825)
    else -> Color(0xFFC62828)
}

private fun severityColor(s: Severity) = when (s) {
    Severity.HIGH -> Color(0xFFC62828)
    Severity.MEDIUM -> Color(0xFFEF6C00)
    Severity.LOW -> Color(0xFFF9A825)
    Severity.INFO -> Color(0xFF546E7A)
}

private fun reportText(r: ScanReport) = buildString {
    appendLine("Solución Scanner · puntaje ${r.score}/100 · ${r.appsScanned} apps")
    r.findings.filter { it.severity != Severity.INFO }.forEach {
        appendLine("[${it.severity}] ${it.title}: ${it.detail}")
    }
}
