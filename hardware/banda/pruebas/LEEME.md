# Sketches de prueba

Cada carpeta tiene un sketch con el mismo nombre (el Arduino IDE lo exige). Son los que se usaron para probar cada componente antes del firmware final. No hacen falta para usar la banda.

| Carpeta | Placa | Fecha | Qué prueba |
|---|---|---|---|
| `prueba_bt_wifi` | ESP32 | 6-nov-2026 | Bluetooth con PIN y escaneo Wi-Fi; `A` enciende el LED del pin 2 y `R` lo apaga |
| `leds_bluetooth` | ESP32 | 6-nov-2026 | LED rojo (GPIO 25) parpadea sin celular; LED azul (GPIO 26) fijo con celular |
| `servo_compuerta` | Arduino UNO | 13-nov-2026 | El servo alterna 0° y 90° cada 5 s |
| `prueba_switches` | Arduino UNO | 13-nov-2026 | Lee S1 (D2) y S2 (D3) y los imprime a 9600 |
| `prueba_motor` | Arduino UNO | 14-nov-2026 | N20 con L293D: 1 s a cada lado y 1 s parado |
| `prueba_l293d` | Arduino UNO | 14-nov-2026 | Revisa las entradas y salidas del L293D |
| `prueba_servo` | Arduino UNO | 14-nov-2026 | El servo va a 0° y a 90° cada 1 s |

Notas:

- **El L293D se quemó y se descartó.** Se calentó por una mala conexión el 14-nov-2026 y el montaje final no lleva driver: el N20 va directo a 5 V. `prueba_motor` y `prueba_l293d` quedan como registro de la prueba, no como parte del montaje.
- El comentario de `prueba_servo` habla de un servo MG996R (el del diseño inicial). El servo del prototipo es un **MG90S**.
- Los sketches se copiaron sin cambios; los comentarios conservan los nombres y pines de esa fecha.
