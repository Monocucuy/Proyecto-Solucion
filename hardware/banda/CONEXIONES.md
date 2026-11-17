# Conexiones de la banda

Fecha: 17-nov-2026. Estado: montaje real del prototipo; pines tomados de los sketches `banda_arduino.ino` y `banda_esp32.ino`.

## Resultado

- Dos cargadores de 5 V, **sin driver de motor**: el N20 va directo a la fuente 1; Arduino, ESP32 y servo comen de la fuente 2. Todo comparte un GND común.
- Arduino UNO: S1 en D2, S2 en D3, servo en D9. ESP32: D32 → D0 del Arduino (órdenes) y, opcional, D1 del Arduino → divisor → D33 (mensajes de vuelta).
- **No se midió ningún voltaje ni corriente** (no hay multímetro). Los valores de las fuentes son los de sus etiquetas.

## Tabla de pines

| Señal | Placa y pin | Se conecta a | Nota |
|---|---|---|---|
| S1 (sensor en la compuerta) | Arduino D2 | Microswitch: NO a D2, común (C) a GND | `INPUT_PULLUP`; presionado = LOW |
| S2 (extremo de la banda) | Arduino D3 | **No instalado** en el prototipo (previsto: NO a D3, C a GND) | `INPUT_PULLUP`; si se instala, solo imprime un aviso |
| Servo MG90S, señal | Arduino D9 | Cable de señal del servo (amarillo o naranja según el fabricante) | |
| Servo MG90S, alimentación | Fuente 2 (5 V, 2 A) | Cable rojo a +5 V; cable marrón a GND común | Directo de la fuente, no del pin 5 V del Arduino |
| Órdenes ESP32 → Arduino | ESP32 D32 (GPIO 32, TX2) | Arduino D0 (RX) | 9600 baudios. **Desconectar al cargar el Arduino** |
| Retorno Arduino → ESP32 (opcional) | Arduino D1 (TX) | 510 Ω en serie hasta ESP32 D33 (GPIO 33, RX2); de D33 a GND una resistencia de 1 kΩ | Divisor de 5 V a 3,3 V; ver más abajo |
| LED rojo | ESP32 GPIO 25 | LED con resistencia de 220 Ω a GND | Parpadea sin celular |
| LED azul | ESP32 GPIO 26 | LED con resistencia de 100 Ω a GND | Fijo con celular (**[NO VERIFICADO]** en la prueba del 13-nov) |
| Alimentación del ESP32 | ESP32 VIN | 5 V del Arduino; GND del ESP32 a GND del Arduino | El USB-C solo no lo energiza |
| Motor N20 | Fuente 1 (5 V, 3 A) | Directo, sin driver | Gira siempre y en un solo sentido |
| D6 y D7 del Arduino | Sin uso | Nada conectado | Ver advertencia 4 |

## Alimentación: las dos fuentes

| Fuente | Alimenta | Cómo llega |
|---|---|---|
| 1. Cargador Xiaomi 5 V, 3 A | Solo el motor N20 | USB macho a una miniplaca reciclada de ventiladores de 5 V, con botón de encendido y 2 puertos USB |
| 2. Cargador Tecno 5 V, 2 A | Arduino, ESP32 (por VIN, desde el Arduino) y servo | Cable largo con un interruptor en el USB |

- Todo el montaje comparte GND. Que el GND de la fuente 1 (la del N20) esté unido al común: **[NO VERIFICADO]** (el dictado dice "todo está unido a un GND común").
- Cómo entra la fuente 2 al Arduino (por el USB o por un pin de 5 V): **[NO VERIFICADO]**.
- Con la radio Bluetooth encendida, el consumo del ESP32 sube de golpe y el Bluetooth necesita voltaje estable. Con la fuente 2 sola, el servo "tiqueaba" sin girar el 14-nov-2026; hoy gira con el GND común. La causa no se confirmó (problemas 6 y 7 de la lista de issues del repositorio: alimentación del servo y del ESP32).

## Divisor del retorno opcional (D1 → D33)

El Arduino saca 5 V por D1 (TX) y el ESP32 solo tolera 3,3 V en sus pines.

```
Arduino D1 (TX) --[ 510 ohm ]--+-- ESP32 D33 (GPIO 33, RX2)
                               |
                            [ 1 kohm ]
                               |
                              GND
```

Cálculo teórico: 5 V × 1000 / (510 + 1000) = 3,31 V en D33. No se midió. Sin este cable la banda funciona igual; el celular solo deja de ver los mensajes del Arduino ("Orden guardada", "Compuerta cerrada"). El ESP32 ya deja D33 con `INPUT_PULLUP` para que no entre ruido si el cable no está.

## Advertencias

1. **No conectar 5 V a ningún pin del ESP32 salvo VIN.** Ni a 3V3 ni a un GPIO. El único cable que trae 5 V desde el Arduino (D1) debe pasar por el divisor. Sin el divisor se daña el ESP32.
2. **Cargar el Arduino con el cable de D0 desconectado.** D0 comparte el puerto serie con el USB.
3. **Unir los GND** de ESP32, Arduino, servo y microswitches. Sin GND común no hay referencia para las señales.
4. **D6 y D7 no se usan, pero el firmware los maneja.** Al arrancar, `banda_arduino.ino` los configura como salidas (IN1 e IN2 del L293D): D6 queda en HIGH y D7 en LOW. No conectar nada ahí sin cambiar el firmware; el cambio no se hizo.
5. **Motor sin driver.** El sentido de giro lo fija cómo se conectan los dos cables del N20; para invertirlo hay que cambiarlos de lugar a mano. La constante `AVANZA` del firmware solo afecta a D6 y D7, o sea, no tiene efecto en el montaje actual.
6. **No volver a usar el L293D** sin revisar el cableado: se calentó por una mala conexión y se dio por quemado (problema 5 de la lista de issues).
7. Una parte de la protoboard no estaba energizada y se halló por prueba y error (problema 7 de la lista de issues). Verificar continuidad antes de culpar al firmware.

## Esquemas y fotos que existen

El esquema del L293D (`esquema_l293d.png`) es **histórico**: el chip se descartó. La foto `banda_switches_posicion.jpg` (14-nov-2026) muestra una versión anterior, con S1 después del servo y con cajas; no representa la posición final de S1. Más en [docs/LEEME_docs.md](docs/LEEME_docs.md).
