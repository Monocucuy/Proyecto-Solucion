// Prueba de los dos microswitch (Arduino UNO).
// S1: un cable a D2, el otro a GND.  S2: un cable a D3, el otro a GND.
// Abrir Monitor Serie a 9600. El LED del pin 13 se enciende si S1 o S2 estan presionados.
const int PIN_S1 = 2;
const int PIN_S2 = 3;

void setup() {
  Serial.begin(9600);
  pinMode(PIN_S1, INPUT_PULLUP);  // sin presionar = HIGH, presionado = LOW
  pinMode(PIN_S2, INPUT_PULLUP);
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
  bool s1 = digitalRead(PIN_S1) == LOW;
  bool s2 = digitalRead(PIN_S2) == LOW;
  digitalWrite(LED_BUILTIN, s1 || s2);
  Serial.print("S1: "); Serial.print(s1 ? "PRESIONADO" : "libre");
  Serial.print("  S2: "); Serial.println(s2 ? "PRESIONADO" : "libre");
  delay(200);
}
