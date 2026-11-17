// Prueba de Bluetooth clasico (SPP) y Wi-Fi para ESP32 clasico.
// Placa: ESP32 Dev Module. Herramientas > Partition Scheme > "Huge APP (3MB No OTA/1MB SPIFFS)".
#include "BluetoothSerial.h"
#include <WiFi.h>

BluetoothSerial SerialBT;

void setup() {
  Serial.begin(115200);
  pinMode(2, OUTPUT);                          // LED azul

  SerialBT.disableSSP();                       // pide PIN fijo en vez de "confirmar codigo"
  bool ok = SerialBT.begin("BANDA-ESP32");     // 1) encender Bluetooth
  bool pin = SerialBT.setPin("1233", 4);       // 2) el PIN va DESPUES de begin()
  Serial.printf("Bluetooth begin=%d, PIN 1233 guardado=%d\n", ok, pin);

  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  int n = WiFi.scanNetworks();
  Serial.printf("Wi-Fi: %d redes encontradas\n", n);
}

void loop() {
  if (SerialBT.available()) {
    char c = SerialBT.read();
    Serial.printf("Recibi: %c\n", c);
    if (c == 'A') { digitalWrite(2, HIGH); SerialBT.println("OK: LED prendido"); }
    if (c == 'R') { digitalWrite(2, LOW);  SerialBT.println("REVISION: LED apagado"); }
  }
}
