// Prueba del chip L293D (Arduino UNO). Sube el codigo y mira los LED o el motor.
// Conexiones del chip (muesca arriba, pin 1 arriba a la izquierda):
//   16 -> 5V Arduino   8 -> 5V Arduino (solo para esta prueba)
//   4, 5, 12, 13 -> GND
//   1 y 9 (enables) -> 5V
//   2 (1A) -> D6    7 (2A) -> D7    10 (3A) -> D8    15 (4A) -> D9
// Salidas: 3 (1Y), 6 (2Y), 11 (3Y), 14 (4Y).
// LED con resistencia de 1k entre una salida Y y GND: debe prender cuando su entrada esta en alto.
// Motor: entre 3 (1Y) y 6 (2Y); gira para un lado en el paso 1 y para el otro en el paso 2.
// Monitor Serie a 9600.
const int ENTRADA[4] = {6, 7, 8, 9};
const int SALIDA_CHIP[4] = {3, 6, 11, 14};

void setup() {
  Serial.begin(9600);
  for (int i = 0; i < 4; i++) pinMode(ENTRADA[i], OUTPUT);
}

void loop() {
  for (int i = 0; i < 4; i++) {
    for (int j = 0; j < 4; j++) digitalWrite(ENTRADA[j], j == i);
    Serial.print("Paso "); Serial.print(i + 1);
    Serial.print(": D"); Serial.print(ENTRADA[i]);
    Serial.print(" en alto -> debe tener voltaje el pin "); Serial.println(SALIDA_CHIP[i]);
    delay(1500);
  }
  for (int j = 0; j < 4; j++) digitalWrite(ENTRADA[j], LOW);
  Serial.println("Todas apagadas");
  delay(1000);
}
