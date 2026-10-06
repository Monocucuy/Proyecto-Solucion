package com.monocucuy.solucion.scan

import android.app.ActivityManager
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.hardware.Sensor
import android.hardware.SensorManager
import android.os.BatteryManager
import android.os.Build
import android.os.Environment
import android.os.PowerManager
import android.os.StatFs
import com.monocucuy.solucion.domain.*

/** Solo APIs públicas: sin root no hay diagnóstico de bajo nivel. */
class HardwareChecker(private val ctx: Context) {

    fun check(): List<Finding> {
        val out = mutableListOf<Finding>()
        val hw = Category.HARDWARE

        // Batería
        val b = ctx.registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
        if (b != null) {
            val temp = b.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, 0) / 10f
            val health = b.getIntExtra(BatteryManager.EXTRA_HEALTH, BatteryManager.BATTERY_HEALTH_UNKNOWN)
            val level = b.getIntExtra(BatteryManager.EXTRA_LEVEL, -1)
            when (health) {
                BatteryManager.BATTERY_HEALTH_OVERHEAT -> out += Finding(hw, Severity.HIGH, "Batería sobrecalentada",
                    "El sistema reporta sobrecalentamiento (${temp}°C).", "Desconecta el cargador y deja enfriar.")
                BatteryManager.BATTERY_HEALTH_DEAD, BatteryManager.BATTERY_HEALTH_UNSPECIFIED_FAILURE ->
                    out += Finding(hw, Severity.HIGH, "Falla de batería", "Estado de salud reportado: falla.", "Llévala a revisión.")
                BatteryManager.BATTERY_HEALTH_OVER_VOLTAGE -> out += Finding(hw, Severity.MEDIUM, "Sobrevoltaje en batería",
                    "El sistema reporta sobrevoltaje.", "Prueba con otro cargador.")
            }
            when {
                temp >= 45f -> out += Finding(hw, Severity.HIGH, "Batería muy caliente", "Temperatura: ${temp}°C.", "Cierra apps pesadas y deja enfriar.")
                temp >= 40f -> out += Finding(hw, Severity.MEDIUM, "Batería caliente", "Temperatura: ${temp}°C.")
            }
            out += Finding(hw, Severity.INFO, "Batería", "Nivel $level% · ${temp}°C")
        }

        // Almacenamiento
        val st = StatFs(Environment.getDataDirectory().path)
        val total = st.totalBytes
        val free = st.availableBytes
        val freePct = (free * 100 / total).toInt()
        val gb = { v: Long -> "%.1f GB".format(v / 1_073_741_824.0) }
        when {
            freePct < 5 -> out += Finding(hw, Severity.HIGH, "Almacenamiento casi lleno", "Libre: ${gb(free)} de ${gb(total)} ($freePct%).", "Libera espacio: fotos, videos y apps sin uso.")
            freePct < 10 -> out += Finding(hw, Severity.MEDIUM, "Poco almacenamiento", "Libre: ${gb(free)} de ${gb(total)} ($freePct%).", "Libera espacio pronto.")
            else -> out += Finding(hw, Severity.INFO, "Almacenamiento", "Libre: ${gb(free)} de ${gb(total)} ($freePct%).")
        }

        // RAM
        val am = ctx.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
        val mi = ActivityManager.MemoryInfo().also { am.getMemoryInfo(it) }
        if (mi.lowMemory) out += Finding(hw, Severity.MEDIUM, "Memoria RAM baja", "El sistema está en estado de poca memoria.", "Cierra apps en segundo plano.")
        out += Finding(hw, Severity.INFO, "RAM", "Disponible ${gb(mi.availMem)} de ${gb(mi.totalMem)}")

        // Térmico
        if (Build.VERSION.SDK_INT >= 29) {
            val pm = ctx.getSystemService(Context.POWER_SERVICE) as PowerManager
            when {
                pm.currentThermalStatus >= PowerManager.THERMAL_STATUS_SEVERE ->
                    out += Finding(hw, Severity.HIGH, "Dispositivo muy caliente", "Estado térmico severo: el sistema está limitando rendimiento.", "Apágalo unos minutos.")
                pm.currentThermalStatus >= PowerManager.THERMAL_STATUS_MODERATE ->
                    out += Finding(hw, Severity.MEDIUM, "Dispositivo caliente", "Estado térmico moderado.")
            }
        }

        // Sensores
        val sm = ctx.getSystemService(Context.SENSOR_SERVICE) as SensorManager
        val count = sm.getSensorList(Sensor.TYPE_ALL).size
        if (sm.getDefaultSensor(Sensor.TYPE_ACCELEROMETER) == null) {
            out += Finding(hw, Severity.LOW, "Sin acelerómetro", "No se detectó acelerómetro; la rotación automática no funcionará.")
        }
        out += Finding(hw, Severity.INFO, "Dispositivo", "${Build.MANUFACTURER} ${Build.MODEL} · $count sensores")
        return out
    }
}
