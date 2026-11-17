// Servo MG996R: va a un lado, espera, va al otro, espera, en bucle.
// Cables: amarillo -> D9, rojo -> + del cargador de 5 V, cafe -> GND del cargador Y GND del Arduino.
#include <Servo.h>

const int PIN_SERVO = 9;
const int ANG_A = 0;        // un lado
const int ANG_B = 90;       // el otro lado (hasta 180)
const unsigned long ESPERA_MS = 1000;

Servo servo;

void setup() {
  servo.attach(PIN_SERVO);
}

void loop() {
  servo.write(ANG_A);
  delay(ESPERA_MS);
  servo.write(ANG_B);
  delay(ESPERA_MS);
}
