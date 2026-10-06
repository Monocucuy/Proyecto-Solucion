# MVP — Proyecto Solución (Android Device Scanner)

> Repo: https://github.com/Monocucuy/Proyecto-Solucion (vacío al momento de escribir este documento)

## 1. Qué es

App Android que hace un chequeo rápido del celular y entrega un reporte de salud en una sola pantalla:

1. **Software/seguridad:** qué apps hay instaladas y cuáles son sospechosas (por hash contra servicios de reputación).
2. **Hardware (lo que Android permite sin root):** batería, almacenamiento, RAM, temperatura, sensores presentes y respondiendo.
3. **Sistema:** versión de Android, parche de seguridad, bloqueo de pantalla, instalación de fuentes desconocidas, opciones de desarrollador/USB debugging.

**Propuesta de valor en una línea:** "Abres la app, tocas Escanear y en menos de 2 minutos sabes si tu celular está sano."

## 2. Fuera del MVP (a propósito)

- Eliminar malware automáticamente (Android no deja a una app normal desinstalar a otras sin confirmación del usuario).
- Escaneo en tiempo real / protección residente.
- Diagnóstico de hardware a bajo nivel (cámara, pantalla táctil, modem). Eso requiere root o apps de fábrica.
- Cuentas de usuario, nube propia, pagos.
- iOS.

## 3. Usuario objetivo

Persona no técnica con un Android que anda lento, se calienta o que instaló una APK de dudosa procedencia, y quiere saber qué pasa sin leer foros.

## 4. Funcionalidades del MVP

### F1. Escaneo de apps instaladas
- Listar apps con `PackageManager`.
- Por cada app de usuario (excluir apps de sistema firmadas por el fabricante): calcular SHA-256 del APK.
- Consultar la reputación del hash en la API de VirusTotal (solo hash, **no se sube el archivo**: privacidad).
- Cache local en Room: un hash ya consultado no se vuelve a consultar por 7 días.
- Resultado por app: Limpia / Sospechosa / Maliciosa / Sin datos.
- Heurísticas locales (no dependen de internet): permisos peligrosos combinados (SMS + accesibilidad + overlay), instalada fuera de Play Store (`getInstallSourceInfo`), app sin ícono visible.

### F2. Diagnóstico de hardware (con APIs públicas)
| Componente | API | Qué se reporta |
|---|---|---|
| Batería | `BatteryManager` | Nivel, temperatura, voltaje, estado de salud reportado, ciclos (Android 14+ si el fabricante lo expone) |
| Almacenamiento | `StatFs`, `StorageStatsManager` | Libre/total, alerta si <10% |
| RAM | `ActivityManager.MemoryInfo` | Total/disponible, bandera de low memory |
| Térmico | `PowerManager.getCurrentThermalStatus()` | Estado térmico actual |
| Sensores | `SensorManager` | Lista de sensores y si responden (lectura de prueba) |
| CPU/Modelo | `Build.*` | Modelo, SoC, ABI |

### F3. Chequeo de configuración del sistema
- Nivel de parche de seguridad (`Build.VERSION.SECURITY_PATCH`) y antigüedad.
- Versión de Android y si sigue recibiendo soporte.
- Bloqueo de pantalla activo (`KeyguardManager.isDeviceSecure`).
- USB debugging / opciones de desarrollador activas.
- Root probable (chequeos simples: binario `su`, build tags `test-keys`).
- Verificación de integridad del dispositivo con **Play Integrity API** (opcional en MVP).

### F4. Reporte
- Puntaje global 0–100 con desglose: Seguridad / Hardware / Sistema.
- Lista de hallazgos ordenada por severidad, con una acción sugerida en lenguaje simple ("Desinstala esta app", "Actualiza Android").
- Exportar reporte como PDF o texto compartible.

## 5. APIs externas (honesto sobre cuáles sirven)

| Servicio | ¿Gratis? | Uso en el MVP | Limitaciones |
|---|---|---|---|
| **VirusTotal API** | Sí, clave gratuita | Consulta por hash (SHA-256) | Aprox. 4 consultas/min y tope diario; uso no comercial. Con 80 apps tomaría ~20 min en frío, por eso el cache y priorizar |
| **MetaDefender Cloud (OPSWAT)** | Sí, cuenta comunitaria | Segunda opinión / respaldo si VT se agota | Cupo diario limitado; la licencia gratuita es para demo/uso personal |
| **Malwarebytes** | **No encontré una API pública gratuita** | No incluir hasta confirmar | Sus integraciones son para empresas. Verifícalo directo con ellos antes de prometerlo en la presentación |
| **Play Integrity API** | Sí (cuota por proyecto en Google Cloud) | Integridad del dispositivo y de la app | Requiere proyecto en Google Cloud y backend para validar el veredicto |

Decisión del MVP: **VirusTotal como motor principal, MetaDefender como respaldo**, y la capa del "tercer servicio" queda como interfaz (`ReputationProvider`) para enchufar otro después.

## 6. Arquitectura

- **Lenguaje:** Kotlin
- **UI:** Jetpack Compose + Material 3
- **Arquitectura:** MVVM + Clean (capas `ui`, `domain`, `data`)
- **Persistencia:** Room (cache de hashes y último reporte)
- **Red:** Retrofit + OkHttp + kotlinx.serialization
- **Tareas largas:** WorkManager (escaneo en segundo plano con notificación de progreso)
- **DI:** Hilt
- **minSdk:** 26 | **targetSdk:** 35

```
app/
 ├─ ui/            # pantallas Compose (Home, Scan, Report, Detail)
 ├─ domain/
 │   ├─ model/     # Finding, Severity, ScanReport
 │   └─ usecase/   # ScanAppsUseCase, HardwareCheckUseCase, SystemCheckUseCase
 ├─ data/
 │   ├─ local/     # Room (HashCacheEntity, ReportEntity)
 │   ├─ remote/    # VirusTotalApi, MetaDefenderApi
 │   └─ repo/      # ReputationProvider (interfaz) + implementaciones
 └─ di/
```

## 7. Pantallas

1. **Home:** botón grande "Escanear", fecha del último escaneo, puntaje anterior.
2. **Escaneo en curso:** progreso por etapa (Apps → Hardware → Sistema), cancelable.
3. **Reporte:** puntaje, tarjetas por categoría, lista de hallazgos.
4. **Detalle de hallazgo:** qué es, por qué importa, qué hacer.
5. **Ajustes:** clave de API propia (el usuario puede pegar la suya), frecuencia de escaneo, exportar.

## 8. Permisos y cumplimiento

- `QUERY_ALL_PACKAGES`: necesario para listar apps. **Google Play lo restringe** y exige justificación; una app de antivirus sí califica, pero hay que declararlo. Para el MVP, distribuir como APK/GitHub Releases evita esa fricción.
- `INTERNET`, `POST_NOTIFICATIONS`, `FOREGROUND_SERVICE` (escaneo largo).
- No se suben APKs; solo hashes. Declarar esto en la política de privacidad.
- Guardar la clave de API en `EncryptedSharedPreferences`, **nunca** hardcodeada en el repo.

## 9. Plan de trabajo (4 semanas)

| Semana | Entregable |
|---|---|
| 1 | Proyecto base, listado de apps, cálculo de hash, pantalla Home |
| 2 | Integración VirusTotal + cache Room + manejo de límite de tasa |
| 3 | Módulos de hardware y sistema + heurísticas locales |
| 4 | Puntaje, reporte, exportar PDF, pruebas en 3 dispositivos distintos, APK de release |

## 10. Criterios de aceptación

- [ ] Escanea ≥50 apps en menos de 3 minutos con cache caliente.
- [ ] Detecta el archivo de prueba EICAR instalado como APK de prueba como "Maliciosa".
- [ ] Funciona sin internet mostrando al menos hardware, sistema y heurísticas locales.
- [ ] No sube ningún archivo del usuario.
- [ ] No crashea si la API devuelve 429 (límite) o está caída.
- [ ] Reporte exportable.

## 11. Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Límite de la API gratuita | Escaneo lento o incompleto | Cache, solo apps de usuario, proveedor de respaldo, clave propia en Ajustes |
| Falsos positivos | Pérdida de confianza | Mostrar "sospechosa" con cantidad de motores, no veredicto absoluto |
| Hardware poco accesible sin root | Promesa inflada | Comunicarlo como "chequeo de salud", no "diagnóstico de fallas" |
| Fabricantes que ocultan datos de batería/térmicos | Datos faltantes | Mostrar "No disponible en este dispositivo" |
| Restricción de Play Store | No publicable | Distribución por APK en la fase inicial |

## 12. Métricas de éxito del MVP

- Tiempo medio de escaneo completo.
- % de apps con veredicto (no "Sin datos").
- Hallazgos accionables por escaneo.
- Crashes por sesión (meta: 0 en pruebas).

## 13. Siguientes pasos después del MVP

- Escaneo programado semanal con notificación.
- Análisis estático de APK (permisos, librerías, URLs embebidas).
- Backend propio para agregar reputación y evitar límites por usuario.
- Comparador "tu celular vs. modelo promedio" (batería, almacenamiento).
