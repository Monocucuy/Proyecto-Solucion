// Banda transportadora - ESP32 (solo Bluetooth).
// Recibe A o R del celular (Serial Bluetooth Terminal) y se la pasa al Arduino por GPIO32 (rotulado D32).
// Conexion: D32 -> D0 (RX) del Arduino, GND comun (el ESP32 ya va alimentado por VIN desde el Arduino).
// OPCIONAL (sin este cable la banda funciona igual): los mensajes del Arduino llegan por D33 y se reenvian al celular.
// Conexion: D1 (TX) del Arduino -> resistencia 510 -> D33 del ESP32, y de D33 -> resistencia 1k -> GND.
// El divisor baja los 5 V del Arduino a 3,3 V: SIN el divisor se dana el ESP32.
// Placa: ESP32 Dev Module. Partition Scheme: Huge APP (3MB No OTA/1MB SPIFFS).
// LED rojo (GPIO 25) parpadea esperando celular; LED azul (GPIO 26) fijo con celular conectado.
#include "BluetoothSerial.h"

const int LED_ROJO = 25;
const int LED_AZUL = 26;
const int TX_ARDUINO = 32;   // D32: salida hacia D0 del Arduino
const int RX_ARDUINO = 33;   // D33: recibe lo que escribe el Arduino (divisor 510 + 1k)

BluetoothSerial SerialBT;

void setup() {
  Serial.begin(115200);
  Serial2.begin(9600, SERIAL_8N1, RX_ARDUINO, TX_ARDUINO);
  pinMode(RX_ARDUINO, INPUT_PULLUP);   // sin cable en D33 no entra ruido
  pinMode(LED_ROJO, OUTPUT);
  pinMode(LED_AZUL, OUTPUT);

  SerialBT.disableSSP();
  SerialBT.begin("BANDA-ESP32");
  SerialBT.setPin("1233", 4);   // el PIN va despues de begin()
}

void loop() {
  bool conectado = SerialBT.hasClient();
  digitalWrite(LED_AZUL, conectado);
  digitalWrite(LED_ROJO, conectado ? LOW : (millis() / 500) % 2);

  while (Serial2.available()) {            // Arduino -> celular
    int b = Serial2.read();
    SerialBT.write(b);
    Serial.write(b);
  }

  while (SerialBT.available()) {
    char c = toupper(SerialBT.read());
    if (c == 'A' || c == 'R') {
      Serial2.write(c);
      SerialBT.print("Enviado: "); SerialBT.println(c);
      Serial.printf("Enviado al Arduino: %c\n", c);
    }
  }
}
