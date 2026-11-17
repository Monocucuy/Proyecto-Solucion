# Banda clasificadora de celulares (Early Access)

Fecha: 17-nov-2026. Estado: **Early Access** (prototipo; se publica como pre-release `v0.2.0-early-access`).

## Resultado

- Es un **prototipo** (no una versión a escala) de una banda transportadora que clasifica celulares: el celular llega a una compuerta, se detiene contra ella y sigue derecho (orden `A`, OK) o se desvía (orden `R`, revisión humana).
- La orden llega por Bluetooth clásico (SPP) a un ESP32, que se la pasa por serie a un Arduino UNO. El Arduino mueve el servo de la compuerta y lee el sensor S1 (dos microswitches en la compuerta). La banda corre siempre.
- Hay pruebas de componentes sueltos y un video del 17-nov-2026 con un celular real contra la compuerta. **No hay** prueba de punta a punta con la app instalada, conteo de pasadas ni medición de velocidad. Detalle en [LIMITACIONES.md](LIMITACIONES.md).

> **Aviso:** la app Android (Solución Scanner) con Bluetooth **no está validada**. La rama `bluetooth-banda` manda la letra al terminar el escaneo, pero no se ha probado en un celular ni de punta a punta con la banda. Para probar la banda use un terminal Bluetooth (sección más abajo).

## Qué hay en esta carpeta

| Ruta | Qué es |
|---|---|
| [`arduino/banda_arduino/banda_arduino.ino`](arduino/banda_arduino/banda_arduino.ino) | Firmware del Arduino UNO (servo, S1, S2, órdenes `A`/`R`) |
| [`esp32/banda_esp32/banda_esp32.ino`](esp32/banda_esp32/banda_esp32.ino) | Firmware del ESP32 (solo puente Bluetooth → serie) |
| [`pruebas/`](pruebas/LEEME.md) | Sketches de prueba de cada componente (uno por carpeta) |
| [CONEXIONES.md](CONEXIONES.md) | Pines, alimentación y advertencias de cableado |
| [CALIBRACION.md](CALIBRACION.md) | Ángulos de la compuerta y cómo ajustarlos |
| [LIMITACIONES.md](LIMITACIONES.md) | Lo que no se probó y lo que no sirve |
| [`docs/`](docs/LEEME_docs.md) | Imágenes y PDF del informe (se agregan después) |
| [`modelo_3d/`](modelo_3d/README.md) | Modelos de Blender: diseño V2 (3-nov) y prototipo final (17-nov) con su `.bat` de render |

## Resumen del montaje

| Parte | Dato |
|---|---|
| Estructura | Lego Technic (set viejo de moto; modelo y número **[NO VERIFICADO]**), con banda de tela cosida |
| Banda (tela) | 11,5 cm de ancho; lazo ≈ 64 cm; tramo visible ≈ 34 cm; grosor ≈ 8 mm (estimado) |
| Estructura | ≈ 45 cm de largo (con soportes) y 10 cm de alto |
| Rodillos | Ruedas de plástico con neumático de caucho (de carritos de control remoto) en ejes de palillo de madera |
| Motor | Motorreductor N20 de 6 V y 50 rpm, alimentado a 5 V directo (sin driver) |
| Compuerta | Micro servo MG90S con una viga Technic como brazo; cerrada, cruza la banda |
| Sensores | 2 microswitches con palanca, ambos en la posición S1 (≈ 4 cm detrás del servo). **S2 no está instalado**; cómo se cablearon los dos de S1 **[NO VERIFICADO]** |
| Controladores | Arduino UNO clon (CH340) para lo mecánico; ESP32 DevKit solo para Bluetooth |
| Alimentación | Dos cargadores de 5 V (3 A para el N20; 2 A para Arduino, ESP32 y servo), con GND común |
| Carga de prueba | Celular de ≈ 300 g. El máximo que aguantaría la banda (≈ 500 g) es una estimación, **no medida** |
| Cajas OK y REVISIÓN | **No hay**: se descartaron en el prototipo |

## Cómo funciona

1. Al encender, el Arduino lleva el servo a 0° (compuerta cerrada) y la banda corre.
2. El celular avanza hasta la compuerta y presiona S1.
3. Si ya hay una orden guardada, la compuerta se abre: `A` a 78° (sigue derecho) o `R` a 33° (se desvía). Si no hay orden, espera e imprime "Celular en la compuerta, esperando orden...".
4. Cuando S1 se suelta (máximo 10 s), la compuerta sigue abierta 3 s y vuelve a 0°. Cada orden se usa una sola vez.
5. S2 (D3) no está instalado en el prototipo. El firmware lo sigue leyendo, pero con `INPUT_PULLUP` y nada conectado nunca se activa; si se instala, solo imprime "S2: algo llego a la caja OK".

## Cargar cada placa

Requisitos: Arduino IDE (la compilación del 15-nov-2026 se hizo con Arduino IDE 2 / arduino-cli), la biblioteca `Servo` (viene con el IDE) y el paquete de placas `esp32` de Espressif (versión usada **[NO VERIFICADO]**).

### Arduino UNO

1. Abrir `arduino/banda_arduino/banda_arduino.ino`.
2. Herramientas → Placa → **Arduino Uno**; elegir el puerto del CH340. Con el Arduino y el ESP32 conectados al PC a la vez aparecen dos CH340.
3. **Quitar el cable que va a D0 (RX) antes de cargar** (D32 del ESP32 → D0 del Arduino). D0 comparte el puerto serie con el USB. Volver a conectarlo al terminar.
4. Cargar. Al reiniciar, el servo va a 0° y el motor queda "corriendo" (en el montaje real el N20 no pasa por el Arduino).

Compilación del 15-nov-2026: 3764 bytes. Los ángulos y los 3 s de retención cambiaron el 17-nov-2026 y **no se recompiló** **[NO VERIFICADO]** que compile igual.

### ESP32

1. Abrir `esp32/banda_esp32/banda_esp32.ino`.
2. Herramientas → Placa → **ESP32 Dev Module**.
3. Herramientas → Partition Scheme → **"Huge APP (3MB No OTA/1MB SPIFFS)"**. Con la partición por defecto, un sketch de prueba del ESP32 con Bluetooth ocupó 121 % y no compiló (nota de estado del 13-nov-2026).
4. Alimentar el ESP32: el USB-C solo no lo energizó. Se alimentó por el pin VIN desde el 5 V del Arduino (con GND común) y con el USB conectado al mismo PC. Ver [CONEXIONES.md](CONEXIONES.md).
5. Cargar. Compilación del 15-nov-2026: 1.061.848 bytes con `PartitionScheme=huge_app`.

El Monitor Serie del ESP32 va a 115200 y muestra "Enviado al Arduino: A" o "R".

## Probar con Serial Bluetooth Terminal (solo Android)

Un iPhone no sirve: no soporta Bluetooth serie clásico.

1. Con la banda encendida, el LED rojo del ESP32 (GPIO 25) parpadea mientras no hay celular.
2. Ajustes de Android → Bluetooth → vincular `BANDA-ESP32`. El celular muestra un aviso "¿Quieres vincular el dispositivo?" y se vincula sin pedir código (el firmware tiene el PIN `1233`; ver [LIMITACIONES.md](LIMITACIONES.md)).
3. Instalar **Serial Bluetooth Terminal** (de Kai Morich, en Play Store).
4. Menú → Devices → pestaña Bluetooth classic → `BANDA-ESP32` → ícono de enchufe. El LED rojo se apaga y el azul (GPIO 26) queda fijo (el azul quedó **[NO VERIFICADO]** en la prueba del 13-nov).
5. Enviar `A` o `R`. El ESP32 responde "Enviado: A" o "Enviado: R".
6. Con un celular contra la compuerta (S1 presionado), la compuerta abre a 78° (`A`) o 33° (`R`). Si la orden llega antes que el celular, queda guardada hasta que S1 se presione.
7. Para ver los mensajes del Arduino en el celular hace falta el retorno opcional D1 → 510 Ω → D33 con 1 kΩ a GND (ver [CONEXIONES.md](CONEXIONES.md)). Sin él, el celular solo ve "Enviado: X".

El comentario del firmware dice que el Monitor Serie del PC a 9600 también puede mandar `A` o `R` al Arduino. Usarlo con el cable D32 → D0 conectado **[NO VERIFICADO]**.

## Más documentación

- [CONEXIONES.md](CONEXIONES.md): tabla de pines, alimentación, advertencias.
- [CALIBRACION.md](CALIBRACION.md): ángulos 0°, 33° y 78°, retención de 3 s.
- [LIMITACIONES.md](LIMITACIONES.md): pruebas que faltan y lo que no sirve.
- [pruebas/LEEME.md](pruebas/LEEME.md): sketches de prueba.
- [docs/LEEME_docs.md](docs/LEEME_docs.md): imágenes y PDF que se agregan después.
- [modelo_3d/README.md](modelo_3d/README.md): archivos de Blender y cómo renderizarlos.
