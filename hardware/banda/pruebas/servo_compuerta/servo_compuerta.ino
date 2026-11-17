// Compuerta de la banda: el servo alterna cerrado/abierto cada 5 s.
// Cables del servo: cafe -> GND, rojo -> 5V (cargador), amarillo -> pin 9.
// El GND del cargador debe ir tambien al GND del Arduino.
#include <Servo.h>

const int PIN_SERVO = 9;
const int ANG_CERRADA = 0;    // ajustar segun el montaje
const int ANG_ABIERTA = 90;   // ajustar segun el montaje
const unsigned long ESPERA_MS = 5000;

Servo compuerta;

void setup() {
  compuerta.attach(PIN_SERVO);
}

void loop() {
  compuerta.write(ANG_CERRADA);  // cierra: el bloque se detiene
  delay(ESPERA_MS);
  compuerta.write(ANG_ABIERTA);  // abre: el bloque cae a la revision
  delay(ESPERA_MS);
}
