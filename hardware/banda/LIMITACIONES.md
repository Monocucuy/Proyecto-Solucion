# Limitaciones de la banda

Fecha: 17-nov-2026. Estado: prototipo en Early Access. Esta lista dice qué **no** se probó y qué no sirve, para que nadie lo dé por hecho.

## Resultado

- Se probaron componentes sueltos y hay un video del 17-nov-2026 con un celular real contra la compuerta. **No** se probó la cadena completa: escaneo en la app, Bluetooth, ESP32, Arduino y compuerta.
- No hay conteo de pasadas, tasa de éxito ni medición de velocidad.
- Solo Android. iOS no sirve.

## Lo que no se probó

| Tema | Estado |
|---|---|
| Prueba de punta a punta con la app instalada (escanear, mandar `A` o `R`, ver la compuerta) | Hecha una vez según el equipo: video del 17-nov-2026, 3:21 a. m. (la app mandó la orden y el servo desvió el celular). Falta repetirla con conteo |
| Rama `bluetooth-banda` de la app | La compila GitHub Actions (no hay Android SDK en el PC del equipo). La versión 0.3.0 se instaló y funcionó en un segundo celular (Xiaomi, Android 16); el vibrador nuevo y la actualización encima de una versión anterior no se han probado |
| Conteo de pasadas y tasa de éxito | No existe. Falta la prueba de 20 pasadas por veredicto que propone el informe de diseño |
| Velocidad de la banda | No se midió. Se describe como lenta; se puede estimar con el video del 17-nov-2026 |
| Sentido de avance | Hacia el extremo del motor N20, deducido de fotos y video **[NO VERIFICADO]** |
| Ángulos 78° y 33° y retención de 3 s | Cambiados el 17-nov-2026 con medidas de fotos; el firmware **no se recompiló** ni se probó con ellos en la banda |
| Carga máxima | El celular de prueba pesa ≈ 300 g. El tope de ≈ 500 g es una estimación **no medida** |
| Par del motor | La ficha del modelo equivalente da ≈ 1,5 kgf·cm; que sea el mismo ejemplar **[NO VERIFICADO]** |
| Voltajes y corrientes | No se midieron (no hay multímetro) |
| LEDs rojo y azul del ESP32 | No hay LED montado: previsto en el firmware, no montado |
| Retorno D1 → D33 | No montado: previsto en el código. Sin este cable el celular no ve los mensajes del Arduino |

## Bluetooth y PIN

- El firmware del ESP32 programa el PIN `1233` con `SerialBT.setPin` después de `begin()`.
- En la práctica, el celular muestra un aviso "¿Quieres vincular el dispositivo?" y se vincula **sin pedir código**. No hay evidencia de que el PIN proteja el ESP32: tratar la banda como sin autenticación.
- Solo Bluetooth clásico (SPP). Un iPhone no soporta Bluetooth serie clásico, así que **iOS no sirve**.

## Comportamiento del firmware que conviene conocer

- Una orden `A` o `R` que llega sin celular en la compuerta queda guardada y se aplica al **siguiente** celular que presione S1. Solo se guarda la última orden, y cada una se usa una sola vez.
- La banda corre siempre: no hay driver, así que no se puede detener ni invertir por software. Lo único que frena al celular es la compuerta cerrada.
- S2 no está instalado (los 2 microswitches que quedan están en S1). Aunque se instale, solo imprime un aviso; no cambia el comportamiento.
- Si S1 no se suelta, la compuerta cierra a los 10 s de todas formas.
- Los pines D6 y D7 siguen configurados como salidas por una versión anterior con L293D, aunque no hay nada conectado ([CONEXIONES.md](CONEXIONES.md)).

## Hardware

- Es un prototipo, no una versión a escala. No hay cajas de OK ni de REVISIÓN: el celular sale por la compuerta o por el lado.
- Arduino, ESP32 y servo comparten una fuente de 5 V y 2 A. El servo "tiqueaba" con ella el 14-nov-2026 y hoy funciona con GND común; la causa no se confirmó.
- Los engranajes del N20 se engrasaron y puede hacer falta más grasa. La tela cosida es la versión final, pero no se midió su desgaste.
- Los microswitches se soldaron "empíricamente" y se pegaron con Super Bonder; S1 ya se rompió una vez.
- Los 10 problemas encontrados se registran como issues abiertos del repositorio.

## Seguridad

Lo que pasó en el taller (humo de soldadura, pegante en los dedos, puntas de palillos, un L293D caliente) está en el problema 10 de la lista de issues. Recomendación (propuesta, no es una norma del equipo): soldar con ventilación, tener cuidado con el Super Bonder y no tocar un chip que se calienta.
