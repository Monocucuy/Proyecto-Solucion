package com.monocucuy.solucion.ui

import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.rotate
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlin.math.cos
import kotlin.math.sin

private val Noche = Color(0xFF0E1A2B)
private val Violeta = Color(0xFF6750A4)
private val Menta = Color(0xFF4ADE80)
private val Ambar = Color(0xFFF9A825)
private val Crema = Color(0xFFF5EBDD)

/**
 * Portada al abrir la app: un celular dibujado que se escanea, sobre la banda clasificadora del proyecto.
 * Todo se dibuja con Canvas (sin imágenes): no pesa y se ve nítido en cualquier pantalla.
 */
@Composable
fun Portada(onEmpezar: () -> Unit) {
    val t = rememberInfiniteTransition(label = "portada")
    val barrido by t.animateFloat(0f, 1f, infiniteRepeatable(tween(1800, easing = LinearEasing), RepeatMode.Reverse), label = "barrido")
    val giro by t.animateFloat(0f, 360f, infiniteRepeatable(tween(2400, easing = LinearEasing)), label = "giro")
    val pulso by t.animateFloat(0.85f, 1f, infiniteRepeatable(tween(900), RepeatMode.Reverse), label = "pulso")

    Column(
        Modifier.fillMaxSize().background(Brush.verticalGradient(listOf(Noche, Color(0xFF2A1F4E), Violeta))),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Spacer(Modifier.height(48.dp))
        Text("PROYECTO SOLUCIÓN", color = Crema.copy(alpha = 0.7f), fontSize = 13.sp, letterSpacing = 4.sp)
        Text("Solución Scanner", color = Color.White, fontSize = 34.sp, fontWeight = FontWeight.Bold)
        Canvas(Modifier.fillMaxWidth().weight(1f).padding(24.dp)) { dibujar(barrido, giro, pulso) }
        Text(
            "Revisa tu celular, decide con datos\ny dale una segunda vida.",
            color = Crema, fontSize = 16.sp, textAlign = TextAlign.Center
        )
        Spacer(Modifier.height(20.dp))
        Button(
            onClick = onEmpezar,
            colors = ButtonDefaults.buttonColors(containerColor = Menta, contentColor = Noche),
            shape = RoundedCornerShape(28.dp),
            modifier = Modifier.fillMaxWidth(0.7f).height(56.dp)
        ) { Text("Empezar", fontSize = 18.sp, fontWeight = FontWeight.Bold) }
        Spacer(Modifier.height(16.dp))
        Text("ETITC · UPN · 2026", color = Crema.copy(alpha = 0.6f), fontSize = 12.sp)
        Spacer(Modifier.height(24.dp))
    }
}

private fun DrawScope.dibujar(barrido: Float, giro: Float, pulso: Float) {
    val w = size.width
    val h = size.height
    // Banda transportadora abajo: dos rodillos que giran y la tela con rayas que avanzan.
    val yBanda = h * 0.86f
    val r = h * 0.05f
    val x1 = w * 0.12f
    val x2 = w * 0.88f
    drawRoundRect(Color(0xFF1F2937), Offset(x1, yBanda - r), Size(x2 - x1, 2 * r), CornerRadius(r, r))
    for (i in 0 until 10) {
        val x = x1 + ((i / 10f + giro / 360f) % 1f) * (x2 - x1)
        drawLine(Crema.copy(alpha = 0.35f), Offset(x, yBanda - r), Offset(x - r * 0.6f, yBanda - r * 0.2f), 3f)
    }
    for (cx in listOf(x1, x2)) {
        drawCircle(Color(0xFF9CA3AF), r, Offset(cx, yBanda))
        rotate(giro, Offset(cx, yBanda)) {
            drawLine(Noche, Offset(cx - r * 0.8f, yBanda), Offset(cx + r * 0.8f, yBanda), 4f)
            drawLine(Noche, Offset(cx, yBanda - r * 0.8f), Offset(cx, yBanda + r * 0.8f), 4f)
        }
    }
    // Compuerta: brazo inclinado (revisión) a la derecha.
    rotate(-35f, Offset(w * 0.74f, yBanda - r)) {
        drawRoundRect(Ambar, Offset(w * 0.74f - 6f, yBanda - r - h * 0.16f), Size(12f, h * 0.16f), CornerRadius(6f, 6f))
    }

    // Celular de pie sobre la banda.
    val pw = w * 0.42f
    val ph = h * 0.66f
    val px = (w - pw) / 2
    val py = yBanda - r - ph - 6f
    drawRoundRect(Color(0xFF111827), Offset(px, py), Size(pw, ph), CornerRadius(pw * 0.14f, pw * 0.14f))
    val m = pw * 0.06f
    drawRoundRect(Color(0xFFFFFBFE), Offset(px + m, py + m * 1.6f), Size(pw - 2 * m, ph - 3.2f * m), CornerRadius(pw * 0.08f, pw * 0.08f))
    drawRoundRect(Color(0xFF111827), Offset(px + pw * 0.4f, py + m * 0.5f), Size(pw * 0.2f, m * 0.6f), CornerRadius(m, m))

    // Anillo de puntaje en la pantalla, con pulso.
    val c = Offset(px + pw / 2, py + ph * 0.36f)
    val ra = pw * 0.26f * pulso
    drawCircle(Color(0xFFE5E7EB), ra, c, style = Stroke(pw * 0.06f))
    drawArc(Menta, -90f, 300f, false, Offset(c.x - ra, c.y - ra), Size(2 * ra, 2 * ra), style = Stroke(pw * 0.06f))
    // Visto bueno dentro del anillo.
    drawLine(Color(0xFF2E7D32), Offset(c.x - ra * 0.4f, c.y), Offset(c.x - ra * 0.1f, c.y + ra * 0.3f), pw * 0.04f)
    drawLine(Color(0xFF2E7D32), Offset(c.x - ra * 0.1f, c.y + ra * 0.3f), Offset(c.x + ra * 0.45f, c.y - ra * 0.35f), pw * 0.04f)
    // Tres barras: seguridad, hardware y sistema.
    val colores = listOf(Menta, Color(0xFF60A5FA), Ambar)
    colores.forEachIndexed { i, col ->
        val y = py + ph * (0.66f + i * 0.08f)
        drawRoundRect(Color(0xFFE5E7EB), Offset(px + 2 * m, y), Size(pw - 4 * m, m * 0.9f), CornerRadius(m, m))
        drawRoundRect(col, Offset(px + 2 * m, y), Size((pw - 4 * m) * (0.95f - i * 0.1f), m * 0.9f), CornerRadius(m, m))
    }
    // Rayo de escaneo que sube y baja por la pantalla.
    val ys = py + m * 2 + barrido * (ph - 4 * m)
    drawRect(
        Brush.verticalGradient(listOf(Color.Transparent, Menta.copy(alpha = 0.45f), Color.Transparent), ys - 30f, ys + 30f),
        Offset(px + m, ys - 30f), Size(pw - 2 * m, 60f)
    )
    drawLine(Menta, Offset(px + m, ys), Offset(px + pw - m, ys), 3f)
    // Ondas de Bluetooth hacia la banda.
    val b = Offset(px + pw + w * 0.05f, py + ph * 0.2f)
    for (k in 1..3) {
        val rr = k * w * 0.03f
        drawArc(Crema.copy(alpha = 0.9f - k * 0.2f), -50f, 100f, false, Offset(b.x - rr, b.y - rr), Size(2 * rr, 2 * rr), style = Stroke(4f))
    }
    // Estrellas vintage de fondo.
    for (i in 0 until 14) {
        val a = i * 0.9f
        val sx = (w * (0.5f + 0.47f * cos(a * 1.7f)))
        val sy = (h * (0.3f + 0.28f * sin(a * 2.3f)))
        if (sx !in px..(px + pw) || sy !in py..(py + ph)) drawCircle(Crema.copy(alpha = 0.25f + 0.2f * pulso), 2.5f, Offset(sx, sy))
    }
}
