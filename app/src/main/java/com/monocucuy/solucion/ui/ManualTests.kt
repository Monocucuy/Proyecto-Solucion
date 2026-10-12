package com.monocucuy.solucion.ui

import android.Manifest
import android.annotation.SuppressLint
import android.content.ActivityNotFoundException
import android.content.Intent
import android.graphics.Bitmap
import android.media.AudioFormat
import android.media.AudioManager
import android.media.AudioRecord
import android.media.MediaRecorder
import android.media.ToneGenerator
import android.provider.MediaStore
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.input.pointer.awaitPointerEventScope
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.onSizeChanged
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.monocucuy.solucion.domain.Category
import com.monocucuy.solucion.domain.Finding
import com.monocucuy.solucion.domain.Severity
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext
import kotlin.math.abs
import kotlin.math.max

/** Pruebas que necesitan que el usuario mire, toque o escuche. Sus resultados entran al próximo escaneo. */
enum class ManualTest(val title: String) {
    SCREEN("Pantalla"), TOUCH("Táctil"), SPEAKER("Altavoz"), MIC("Micrófono"), CAMERA("Cámara")
}

@Composable
fun ManualTestsList(results: Map<ManualTest, Finding>, onRun: (ManualTest) -> Unit, onBack: () -> Unit) = Column(
    Modifier.fillMaxSize().padding(16.dp),
    verticalArrangement = Arrangement.spacedBy(8.dp)
) {
    Text("Pruebas manuales", fontSize = 22.sp, fontWeight = FontWeight.Bold)
    Text("Los resultados se incluyen en el próximo escaneo.", fontSize = 13.sp)
    ManualTest.values().forEach { t ->
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(12.dp)) {
                Text(t.title, fontWeight = FontWeight.SemiBold)
                Text(results[t]?.let { "Último: ${it.title}" } ?: "Sin probar", fontSize = 13.sp)
                OutlinedButton(onClick = { onRun(t) }) { Text("Probar") }
            }
        }
    }
    Spacer(Modifier.height(8.dp))
    TextButton(onClick = onBack) { Text("Volver") }
}

/** Ejecuta una prueba. [onDone] recibe el resultado, o null si el usuario sale sin terminar. */
@Composable
fun ManualTestHost(test: ManualTest, onDone: (Finding?) -> Unit) = when (test) {
    ManualTest.SCREEN -> ScreenTest(onDone)
    ManualTest.TOUCH -> TouchTest(onDone)
    ManualTest.SPEAKER -> SpeakerTest(onDone)
    ManualTest.MIC -> MicTest(onDone)
    ManualTest.CAMERA -> CameraTest(onDone)
}

@Composable
private fun ScreenTest(onDone: (Finding?) -> Unit) {
    val colors = listOf(Color.Black, Color.White, Color.Red, Color.Green, Color.Blue)
    var i by remember { mutableIntStateOf(0) }
    if (i < colors.size) {
        Box(Modifier.fillMaxSize().background(colors[i]).clickable { i++ }, contentAlignment = Alignment.Center) {
            Text("Toca para seguir (${i + 1}/${colors.size})",
                color = if (colors[i] == Color.Black) Color.White else Color.Black)
        }
    } else {
        Column(Modifier.fillMaxSize().padding(24.dp), verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally) {
            Text("¿Viste manchas, líneas o píxeles muertos?", fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
            Spacer(Modifier.height(16.dp))
            Button(onClick = {
                onDone(Finding(Category.HARDWARE, Severity.INFO, "Pantalla: sin defectos visibles",
                    "Revisión visual en 5 colores."))
            }) { Text("No") }
            Spacer(Modifier.height(8.dp))
            OutlinedButton(onClick = {
                onDone(Finding(Category.HARDWARE, Severity.MEDIUM, "Pantalla: defecto visible",
                    "Manchas, líneas o píxeles muertos en la revisión.",
                    "Si está en garantía, revísala en servicio técnico."))
            }) { Text("Sí") }
        }
    }
}

@Composable
private fun TouchTest(onDone: (Finding?) -> Unit) {
    val cols = 12
    val rows = 20
    val hit = remember { mutableStateMapOf<Int, Boolean>() }
    var boxSize by remember { mutableStateOf(IntSize.Zero) }

    fun mark(p: Offset) {
        if (boxSize.width == 0 || boxSize.height == 0) return
        val c = (p.x * cols / boxSize.width).toInt().coerceIn(0, cols - 1)
        val r = (p.y * rows / boxSize.height).toInt().coerceIn(0, rows - 1)
        hit[r * cols + c] = true
    }

    val pct = hit.count { it.value } * 100 / (cols * rows)
    Column(Modifier.fillMaxSize()) {
        Text("Desliza el dedo por toda la pantalla hasta pintar la cuadrícula.",
            modifier = Modifier.padding(12.dp), fontSize = 14.sp)
        Canvas(
            Modifier.weight(1f).fillMaxWidth()
                .onSizeChanged { boxSize = it }
                .pointerInput(Unit) {
                    awaitPointerEventScope {
                        while (true) {
                            awaitPointerEvent().changes.forEach { if (it.pressed) mark(it.position) }
                        }
                    }
                }
        ) {
            val cw = this.size.width / cols
            val ch = this.size.height / rows
            for (r in 0 until rows) for (c in 0 until cols) {
                val done = hit[r * cols + c] == true
                drawRect(
                    color = if (done) Color(0xFF2E7D32) else Color(0xFFE0E0E0),
                    topLeft = Offset(c * cw, r * ch),
                    size = Size(cw - 1, ch - 1)
                )
            }
        }
        Row(Modifier.fillMaxWidth().padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
            Text("Cubierto: $pct%", Modifier.weight(1f))
            Button(onClick = {
                onDone(if (pct >= 90) {
                    Finding(Category.HARDWARE, Severity.INFO, "Táctil: responde en $pct% de la pantalla",
                        "Cuadrícula de ${cols}x$rows.")
                } else {
                    Finding(Category.HARDWARE, Severity.MEDIUM, "Táctil: zonas sin respuesta",
                        "Solo $pct% respondió al deslizar.",
                        "Limpia la pantalla y repite; si persiste, lleva el equipo a revisión.")
                })
            }) { Text("Terminar") }
        }
    }
}

@Composable
private fun SpeakerTest(onDone: (Finding?) -> Unit) {
    var played by remember { mutableStateOf(false) }
    LaunchedEffect(Unit) {
        val tone = runCatching { ToneGenerator(AudioManager.STREAM_MUSIC, 100) }.getOrNull()
        tone?.startTone(ToneGenerator.TONE_PROP_BEEP, 800)
        try {
            delay(1_000)
        } finally {
            tone?.release()
        }
        played = true
    }
    Column(Modifier.fillMaxSize().padding(24.dp), verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally) {
        if (!played) {
            Text("Reproduciendo tono…")
        } else {
            Text("¿Escuchaste el tono?", fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
            Spacer(Modifier.height(16.dp))
            Button(onClick = {
                onDone(Finding(Category.HARDWARE, Severity.INFO, "Altavoz: tono audible", "Confirmado por el usuario."))
            }) { Text("Sí") }
            Spacer(Modifier.height(8.dp))
            OutlinedButton(onClick = {
                onDone(Finding(Category.HARDWARE, Severity.MEDIUM, "Altavoz: no se escuchó el tono",
                    "Sin tono confirmado por el usuario.", "Revisa el volumen de medios o si el altavoz está tapado."))
            }) { Text("No") }
        }
    }
}

private enum class MicPhase { IDLE, RECORDING, DENIED, DONE }

@Composable
private fun MicTest(onDone: (Finding?) -> Unit) {
    var phase by remember { mutableStateOf(MicPhase.IDLE) }
    var peak by remember { mutableIntStateOf(-1) }
    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        phase = if (granted) MicPhase.RECORDING else MicPhase.DENIED
    }
    LaunchedEffect(phase) {
        if (phase == MicPhase.RECORDING) {
            peak = runCatching { recordPeak() }.getOrDefault(-1)
            phase = MicPhase.DONE
        }
    }
    Column(Modifier.fillMaxSize().padding(24.dp), verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally) {
        when (phase) {
            MicPhase.IDLE -> {
                Text("Al empezar, habla durante 3 segundos.")
                Spacer(Modifier.height(16.dp))
                Button(onClick = { launcher.launch(Manifest.permission.RECORD_AUDIO) }) { Text("Empezar") }
            }
            MicPhase.RECORDING -> Text("Grabando 3 s… habla ahora.")
            MicPhase.DENIED -> {
                Text("Sin permiso de micrófono; la prueba no se realizó.")
                Spacer(Modifier.height(16.dp))
                OutlinedButton(onClick = {
                    onDone(Finding(Category.HARDWARE, Severity.INFO, "Micrófono: prueba no realizada", "Permiso denegado."))
                }) { Text("Cerrar") }
            }
            MicPhase.DONE -> {
                val pct = max(peak, 0) * 100 / 32767
                if (peak < 0) {
                    Text("No se pudo abrir el micrófono.")
                } else {
                    Text("Pico de audio: $pct%")
                }
                Spacer(Modifier.height(16.dp))
                Button(onClick = {
                    onDone(when {
                        peak < 0 -> Finding(Category.HARDWARE, Severity.MEDIUM, "Micrófono: no se pudo abrir",
                            "El sistema no entregó audio.", "Revisa si otra app lo está usando.")
                        peak >= MIC_THRESHOLD -> Finding(Category.HARDWARE, Severity.INFO, "Micrófono: capta audio",
                            "Pico de $pct% durante 3 s.")
                        else -> Finding(Category.HARDWARE, Severity.MEDIUM, "Micrófono sin señal",
                            "Pico de $pct% durante 3 s: no se captó voz.",
                            "Repite hablando cerca; si persiste, revisa el micrófono.")
                    })
                }) { Text("Guardar resultado") }
            }
        }
    }
}

/** Graba 3 s y devuelve el pico absoluto (0..32767). -1 si el micrófono no abre. */
@SuppressLint("MissingPermission")
private suspend fun recordPeak(): Int = withContext(Dispatchers.IO) {
    val rate = 16_000
    val minBuf = AudioRecord.getMinBufferSize(rate, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT)
    if (minBuf <= 0) return@withContext -1
    val rec = AudioRecord(MediaRecorder.AudioSource.MIC, rate, AudioFormat.CHANNEL_IN_MONO,
        AudioFormat.ENCODING_PCM_16BIT, minBuf * 2)
    try {
        if (rec.state != AudioRecord.STATE_INITIALIZED) return@withContext -1
        val buf = ShortArray(minBuf)
        var peak = 0
        rec.startRecording()
        val end = System.currentTimeMillis() + 3_000
        while (System.currentTimeMillis() < end) {
            val n = rec.read(buf, 0, buf.size)
            for (i in 0 until n.coerceAtLeast(0)) peak = max(peak, abs(buf[i].toInt()))
        }
        peak
    } finally {
        rec.release()
    }
}

private const val MIC_THRESHOLD = 1_500 // ~4,5 % de escala: por debajo es ruido de fondo

@Composable
private fun CameraTest(onDone: (Finding?) -> Unit) {
    var photo by remember { mutableStateOf<Bitmap?>(null) }
    var failed by remember { mutableStateOf(false) }
    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.StartActivityForResult()) { res ->
        photo = res.data?.extras?.get("data") as? Bitmap
        failed = photo == null
    }
    LaunchedEffect(Unit) {
        try {
            launcher.launch(Intent(MediaStore.ACTION_IMAGE_CAPTURE))
        } catch (e: ActivityNotFoundException) {
            failed = true
        }
    }
    Column(Modifier.fillMaxSize().padding(24.dp), verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally) {
        val bmp = photo
        when {
            bmp != null -> {
                Image(bitmap = bmp.asImageBitmap(), contentDescription = null,
                    modifier = Modifier.fillMaxWidth().height(240.dp))
                Spacer(Modifier.height(12.dp))
                Text("¿La foto se ve bien?", fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
                Spacer(Modifier.height(8.dp))
                Button(onClick = {
                    onDone(Finding(Category.HARDWARE, Severity.INFO, "Cámara: captura correcta", "Confirmado por el usuario."))
                }) { Text("Sí") }
                Spacer(Modifier.height(8.dp))
                OutlinedButton(onClick = {
                    onDone(Finding(Category.HARDWARE, Severity.MEDIUM, "Cámara: foto con fallas",
                        "El usuario reportó una foto mala.", "Revisa lente, enfoque o suciedad."))
                }) { Text("No") }
            }
            failed -> {
                Text("No se tomó foto o no hay app de cámara.")
                Spacer(Modifier.height(16.dp))
                OutlinedButton(onClick = {
                    onDone(Finding(Category.HARDWARE, Severity.INFO, "Cámara: prueba no realizada",
                        "Sin foto ni app de cámara disponible."))
                }) { Text("Cerrar") }
            }
            else -> Text("Abriendo la cámara…")
        }
    }
}
