# v0.3.0-early-access (pre-release)

Fecha: 17-nov-2026. App **Solución Scanner 0.3.0** + firmware de la banda. Documentación técnica de la app: [`docs/APP.md`](https://github.com/Monocucuy/Proyecto-Solucion/blob/bluetooth-banda/docs/APP.md).

## Qué cambió

- **Portada** animada al abrir la app.
- **Botones de volver y cancelar** en el escaneo, el reporte, la lista de pruebas manuales y cada prueba.
- **Vibrador**: pulsos a intensidad máxima (uso alarma) y botón "Vibrar otra vez"; antes no se sentía en Xiaomi/Redmi.
- **Bluetooth**: si la conexión segura falla ("read failed"), reintenta con la insegura.
- **Actualizar**: todas las APK de prueba se firman con la misma llave y el número de versión siempre sube.

> **Importante:** si tienes una APK anterior (0.1 o 0.2), desinstálala **una sola vez** antes de instalar esta. Desde la 0.3.0 las siguientes se actualizan encima.

## Instalar

1. Descarga `solucion-scanner-early-access-debug.apk` desde el celular.
2. Permite instalar apps de orígenes desconocidos para el navegador.
3. Google Play Protect avisa que la app no está verificada: **Más detalles → Instalar de todas formas**.
4. Si pregunta si quieres enviar la app a Google para revisarla: **No enviar**.
5. Acepta el permiso de Bluetooth (dispositivos cercanos), vincula `BANDA-ESP32` en Ajustes y escanea.

Veredicto: menos de 80 puntos manda `R` (revisión humana); 80 o más manda `A`. Las correcciones de esta versión **no se han probado** todavía en el celular del equipo.

---

# Notas de v0.2.0-early-access

Fecha: 17-nov-2026. Estado: **Early Access**. Es una pre-release: la app con Bluetooth y la banda transportadora **no están validadas de punta a punta**.

## Resultado

- Trae la APK de depuración de la app **Solución Scanner** (rama `bluetooth-banda`), el firmware de la banda (Arduino y ESP32) y el informe técnico final.
- Si esta release existe, GitHub Actions compiló la app y pasó las pruebas unitarias. Eso **no** prueba que la app funcione en un celular ni con la banda.
- Para probar la banda, use un terminal Bluetooth (ver `hardware/banda/README.md` dentro del zip).

## Qué incluye

| Archivo | Qué es |
|---|---|
| `solucion-scanner-early-access-debug.apk` | APK de depuración (versión de la app `0.1.0-mvp`), compilada por GitHub Actions desde la rama `bluetooth-banda`. Firmada con la clave de depuración. Solo para pruebas |
| `firmware-banda-early-access.zip` | Carpeta `hardware/banda/`: firmware del Arduino UNO y del ESP32, sketches de prueba, conexiones, calibración y limitaciones |
| `Informe_Tecnico_Final_Banda_Clasificadora.pdf` | Informe técnico final (solo está si el PDF existía en el repositorio al publicar) |

## Qué NO está validado

- **App con Bluetooth**: manda la letra `A` o `R` al `BANDA-ESP32` al terminar el escaneo. Nunca se probó en un celular con la banda; no hay prueba de punta a punta. La app está en espera.
- **Veredicto**: en la rama publicada, `UMBRAL_REVISION` es 80 (`bt/BandaBluetooth.kt`); el manual de usuario habla de 70 puntos. Además, una prueba manual fallida es severidad MEDIA (resta 8) y no fuerza la revisión. Diferencias conocidas, sin resolver. Confirmar contra el commit de la etiqueta.
- **Firmware**: los ángulos de la compuerta (78° y 33°) y la retención de 3 s se cambiaron el 17-nov-2026 y el firmware **no se recompiló** desde entonces. Última compilación (15-nov-2026): Arduino UNO 3764 bytes; ESP32 1.061.848 bytes con `PartitionScheme=huge_app`.
- **Banda**: sin conteo de pasadas, tasa de éxito ni medición de velocidad. Hay un video del 17-nov-2026 con un celular real (≈ 300 g) contra la compuerta; no se suben los videos.
- **PIN `1233`**: está en el firmware del ESP32, pero el celular solo muestra un aviso de vinculación y no pide código. No cuente con él como protección.
- Problemas abiertos del prototipo: ver los issues con la etiqueta `banda-transportadora`.

## Cómo instalar la APK

Requiere Android 8.0 (API 26) o superior. iOS no sirve.

1. Bajar `solucion-scanner-early-access-debug.apk` desde esta página, con el navegador del celular.
2. Abrirla. Android pide permiso para instalar apps de orígenes desconocidos para ese navegador o gestor de archivos: concederlo solo para esta instalación.
3. Instalar y abrir **Solución Scanner**.
4. En Android 12 o superior, aceptar el permiso de Bluetooth (`BLUETOOTH_CONNECT`) cuando la app lo pida.
5. Opcional, no recomendado (en las pruebas tardaba más de 5 minutos): en **Ajustes**, pegar una clave de VirusTotal. Sin clave, la app corre hardware, sistema y heurísticas locales y omite la reputación por hash.

Si ya tiene instalada otra APK de este repositorio (por ejemplo la de la release `apk-debug`) y Android rechaza la instalación, desinstale la anterior primero: las APK de depuración compiladas en ejecuciones distintas pueden venir firmadas con claves distintas **[NO VERIFICADO en este repositorio]**.

## Cómo vincular el ESP32

1. Cargar el firmware del ESP32 y energizarlo (el USB-C solo no lo energiza; ver `CONEXIONES.md` en el zip).
2. En Ajustes de Android → Bluetooth, vincular `BANDA-ESP32`. El celular muestra "¿Quieres vincular el dispositivo?" y se vincula sin pedir código.
3. Hacerlo **antes** de escanear: la app busca `BANDA-ESP32` entre los dispositivos ya vinculados. Si no lo encuentra, el fallo de Bluetooth no cancela el escaneo.
4. Para probar sin la app: instalar Serial Bluetooth Terminal (Kai Morich), conectarse a `BANDA-ESP32` y enviar `A` o `R`. El ESP32 responde "Enviado: A" o "Enviado: R".

## Límites

- Solo Android; un iPhone no soporta Bluetooth serie clásico.
- Es un prototipo (Lego Technic y tela), no una versión a escala. No tiene cajas de OK ni de REVISIÓN.
- La banda corre siempre y en un solo sentido; el N20 va directo a 5 V, sin driver.
- Carga de prueba ≈ 300 g. El máximo de ≈ 500 g es una estimación, **no medida**.
- La APK es de depuración: no es una versión para Google Play.

## Esta release no toca otras

Se publica con una etiqueta `v*-early-access` propia. No borra ni reemplaza la release `apk-debug` ni otras.
