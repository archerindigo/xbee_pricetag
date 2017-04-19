#include <SoftwareSerial.h>
// Define pin
SoftwareSerial PC(9, 10);

void setup() {
  Serial.begin(9600);
  PC.begin(115200);
  PC.println("Start");
}

void loop() {
  if(Serial.available()) {
    PC.print(Serial.read(), HEX);
    PC.print(' ');
  }
  if(PC.available()) {
    Serial.write(PC.read());
  }
}

