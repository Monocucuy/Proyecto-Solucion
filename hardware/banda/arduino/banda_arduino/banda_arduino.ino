// Banda transportadora - Arduino UNO (parte mecanica). La banda corre SIEMPRE.
// El servo es una COMPUERTA que normalmente esta CERRADA: el celular llega a S1 y espera contra ella.
// El celular (app -> ESP32 -> D0, o Monitor Serie del PC a 9600) manda una letra:
//   A = sin revision humana: la compuerta se abre COMPLETA y el celular sigue derecho.
//   R = necesita revision humana: la compuerta se abre solo un angulo corto y la banda lo desvia a la caja de revision.
// Cuando el celular termina de pasar (S1 se suelta) la compuerta vuelve a cerrarse.
// Si la orden llega antes que el celular, se guarda y se usa cuando toque S1. Cada orden se usa una sola vez.
// S2 (final de la banda) solo avisa por serie que algo llego a la caja OK.
//
// Conexiones:
//   S1: C -> GND, NO -> D2      S2: C -> GND, NO -> D3
//   L293D: pin 2 -> D6, pin 7 -> D7, motor en los pines 3 y 6 (el resto como en el esquema)
//   Servo: cafe -> GND, rojo -> 5V del cargador, amarillo -> D9 (GND del cargador unido al del Arduino)
//   ESP32: D32 -> D0 (RX). Desconectar ese cable al subir el programa.
#include <Servo.h>

const int PIN_S1 = 2;
const int PIN_S2 = 3;
const int IN1 = 6;
const int IN2 = 7;
const int PIN_SERVO = 9;

const int ANG_CERRADA = 0;     // al prender o reiniciar el Arduino el servo va aqui y bloquea el paso
// Angulos medidos de las fotos del 17-nov-2026 (la compuerta cerrada cruza la banda; 0 = esa posicion):
//   ANG_ABIERTA 78  -> el brazo queda casi pegado al borde de la banda (foto 3), ya no se pasa de largo.
//   ANG_REVISION 33 -> brazo en diagonal (foto 4). Si queda corto o largo, mover 3-5 grados y volver a probar.
const int ANG_REVISION = 33;   // abertura corta: la banda desvia el celular a la caja de revision
const int ANG_ABIERTA = 78;    // abertura completa: sigue derecho
const bool AVANZA = HIGH;      // si la banda va al reves, poner LOW
const unsigned long PASO_MS = 3000;   // tras soltarse S1, la compuerta sigue abierta (OK o revision) este tiempo antes de cerrar
const unsigned long MAX_ABIERTA_MS = 10000;  // si S1 no se suelta, cierra igual a los 10 s

Servo compuerta;
char orden = 0;                // ultima orden recibida y aun no usada
bool esperando = false, s2Antes = false;

void motor(bool corre) {
  digitalWrite(IN1, corre ? AVANZA : LOW);
  digitalWrite(IN2, corre ? !AVANZA : LOW);
}

bool presionado(int pin) { return digitalRead(pin) == LOW; }

void leerSerie() {
  while (Serial.available()) {
    char c = toupper(Serial.read());
    if (c == 'A' || c == 'R') {
      orden = c;
      Serial.print("Orden guardada: "); Serial.println(c);
    }
  }
}

void pasar(char destino) {
  Serial.println(destino == 'R' ? "REVISION: compuerta en diagonal" : "OK: compuerta abierta completa");
  compuerta.write(destino == 'R' ? ANG_REVISION : ANG_ABIERTA);
  unsigned long t0 = millis();
  while (presionado(PIN_S1) && millis() - t0 < MAX_ABIERTA_MS) {}   // espera que el celular termine de pasar
  delay(PASO_MS);
  compuerta.write(ANG_CERRADA);
  Serial.println("Compuerta cerrada");
}

void setup() {
  Serial.begin(9600);
  pinMode(PIN_S1, INPUT_PULLUP);
  pinMode(PIN_S2, INPUT_PULLUP);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  compuerta.attach(PIN_SERVO);   // queda energizado para sostener la compuerta cerrada
  compuerta.write(ANG_CERRADA);
  motor(true);
  Serial.println("Banda corriendo, compuerta cerrada. Enviar A (ok) o R (revision).");
}

void loop() {
  leerSerie();

  if (presionado(PIN_S1)) {                   // hay un celular contra la compuerta
    if (orden) {
      char destino = orden;
      orden = 0;
      esperando = false;
      pasar(destino);
    } else if (!esperando) {
      esperando = true;
      Serial.println("Celular en la compuerta, esperando orden...");
    }
  } else {
    esperando = false;
  }

  bool s2 = presionado(PIN_S2);
  if (s2 && !s2Antes) Serial.println("S2: algo llego a la caja OK");
  s2Antes = s2;
}
