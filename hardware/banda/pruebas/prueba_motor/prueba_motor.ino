// Motor N20 con L293D: 1 s a la derecha, 1 s parado, 1 s a la izquierda, 1 s parado, en bucle.
// Chip (muesca arriba): 16, 8 y 1 -> 5V | 4, 5, 12, 13 -> GND | pin 2 -> D6 | pin 7 -> D7
// Motor entre los pines 3 y 6 del chip. Si "derecha" sale al reves, cambia los cables del motor entre si.
const int IN1 = 6;   // pin 2 del chip
const int IN2 = 7;   // pin 7 del chip
const unsigned long MS = 1000;

void mover(bool a, bool b) {
  digitalWrite(IN1, a);
  digitalWrite(IN2, b);
  delay(MS);
}

void setup() {
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
}

void loop() {
  mover(HIGH, LOW);   // derecha
  mover(LOW, LOW);    // parado
  mover(LOW, HIGH);   // izquierda
  mover(LOW, LOW);    // parado
}
