// Dos LED de estado para el Bluetooth del ESP32.
// Rojo (GPIO 25): parpadea mientras espera que un celular se conecte.
// Azul (GPIO 26): fijo mientras hay un celular conectado.
// Placa: ESP32 Dev Module. Partition Scheme: Huge APP (3MB No OTA/1MB SPIFFS).
#include "BluetoothSerial.h"

const int LED_ROJO = 25;
const int LED_AZUL = 26;

BluetoothSerial SerialBT;

void setup() {
  Serial.begin(115200);
  pinMode(LED_ROJO, OUTPUT);
  pinMode(LED_AZUL, OUTPUT);

  SerialBT.disableSSP();
  bool ok = SerialBT.begin("BANDA-ESP32");
  bool pin = SerialBT.setPin("1233", 4);       // el PIN va despues de begin()
  Serial.printf("Bluetooth begin=%d, PIN 1233 guardado=%d\n", ok, pin);
}

void loop() {
  static bool estabaConectado = false;
  bool conectado = SerialBT.hasClient();

  if (conectado) {
    digitalWrite(LED_ROJO, LOW);
    digitalWrite(LED_AZUL, HIGH);
  } else {
    digitalWrite(LED_AZUL, LOW);
    digitalWrite(LED_ROJO, (millis() / 500) % 2);   // parpadea cada 0,5 s
  }

  if (conectado != estabaConectado) {
    Serial.println(conectado ? "Celular conectado" : "Celular desconectado");
    estabaConectado = conectado;
  }

  while (SerialBT.available()) Serial.write(SerialBT.read());   // lo que llegue del celular
}
