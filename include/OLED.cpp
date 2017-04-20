#include <SPI.h>
#include <Wire.h>
#include "Adafruit_SSD1306.h"
#include "ArduinoJson.h"

#define OLED_RESET 4

extern float price;
extern String p_name;
extern Adafruit_SSD1306 Display;

String FloatToString(double val, int dec, int dig ) {
  int addpad = 0;
  char sbuf[20];
  String fdata = (dtostrf(val, dec, dig, sbuf));
  int slen = fdata.length();
  for ( addpad = 1; addpad <= dec + dig - slen; addpad++) {
    fdata = " " + fdata;
  }
  return (fdata);
}

void OLED_display() {
  Display.clearDisplay();
  Display.setTextColor(WHITE);
  Display.setTextSize(1);
  Display.setCursor(0, 0);
  Display.println(p_name);
  Display.setTextSize(2);
  Display.setCursor(0, 10);
  Display.println("$");
  Display.setTextSize(3);
  Display.setCursor(16, 10);
  Display.println(FloatToString(price, 5, 1));
  Display.display();
}

void Get_JSON(char json[]) {
  StaticJsonBuffer<200> jsonBuffer;
  JsonObject& product = jsonBuffer.parseObject(json);
  const char* p_temp = product["p_name"];
  p_name = p_temp;
  price = product["price"];
}
