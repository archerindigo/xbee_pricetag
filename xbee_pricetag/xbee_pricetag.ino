/*
 * The Chinese University of Hong Kong
 * CENG 3410 - Smart Hardware Design
 * Project: Smart Price Tags
 * 
 * Arduino Xbee Price Tag Controller
 * Author: Terry Tsang, Hing, Alan
 * 
 * v0.1.0 (20/4/2017)
 */

#include <SoftwareSerial.h>
#include "simpleXbee.h"
#include "Adafruit_SSD1306.h"
#include "OLED.h"
//#include "ArduinoJson.h"

#define OLED_RESET 4

// Global variables
SoftwareSerial PCss(9, 10);
RxPacket* rx = new RxPacket(); // instance of RxPackage
Adafruit_SSD1306 Display(OLED_RESET);
byte buff[60];
int updateSignal = 0;
float price = 1234.5;
char p_name[21] = "CENG3410 Price Tag";
//DynamicJsonBuffer jsonBuffer;

void setup() {
  // put your setup code here, to run once:
  Display.begin(SSD1306_SWITCHCAPVCC, 0x3C);  // initialize with the I2C addr 0x3C
  OLED_display(); // Display default text
  Serial.begin(9600);
  PCss.begin(9600);
  PCss.println("Start");
}

void loop() {
  /* 
   *  1. Handle serial event
   */
  
  if (Serial.available()) {
    // got something from Xbee

    if (Serial.read() == 0x7E) {
      // got start of frame
      PCss.println("Receiving frame");
      rx = new RxPacket(); // Reset packet instance

      // Read packet length
      Serial.readBytes(buff, 2);
      rx->setPackageLength(buff);
      PCss.print("Length of packet: ");
      PCss.println(rx->getPackageLength());

      // Read frame type
      byte frameType;
      Serial.readBytes(&frameType, 1);
//      PCss.print("Frame type: ");
//      PCss.println(frameType, HEX);
      if (frameType != 0x90) {
        // Invalid packet, reset and wait for next rx
//        PCss.println("Not a Rx packet");
        rx = new RxPacket(); // Reset packet instance
        return;
      }
      
      // Read 64-bit address
      Serial.readBytes(buff, 8);
      rx->setSA64(buff);
      PCss.print("64-bit addr: ");
      debug_printBytes(rx->getSA64(), 8);

      // Read 16-bit address
      Serial.readBytes(buff, 2);
      rx->setSA16(buff);
      PCss.print("16-bit addr: ");
      debug_printBytes(rx->getSA16(), 2);

      // Read receive option
      Serial.readBytes(buff, 1);
      rx->setRO(buff[0]);
      PCss.print("RO: ");
      PCss.println(rx->getRO(), HEX);
      
      // Read data
      Serial.readBytes(buff, rx->getDataLength());
      rx->setData(buff);
      PCss.print("Payload(HEX): ");
      debug_printBytes(rx->getData(), rx->getDataLength());
      PCss.print("Payload(ASCII): ");
      PCss.println((char*)rx->getData());

      // Read checksum and compare
      Serial.readBytes(buff, 1);
      rx->setChecksum(buff[0]);
      PCss.print("Received Checksum: ");
      PCss.println(rx->getChecksum(), HEX);
      PCss.print("Calculated Checksum: ");
      PCss.println(rx->calcChecksum(), HEX);
      if (rx->checkChecksum()) {
//        PCss.println("Checksum matched");
        updateSignal = 1; // Prepare to update tag
        delay(100);  // Let serial print finish
      }
      else {
//        PCss.println("Checksum not matched, discarding packet");
        rx = new RxPacket();
      }
    }
  }

  /*
   * 2. Update tag
   */
  if (updateSignal) {
    updateSignal = 0;  // Reset signal
    Get_JSON((char*)rx->getData());
    PCss.print("p_name = ");
    PCss.println(p_name);
    PCss.print("price = ");
    PCss.println(price);
    OLED_display();
  }
}

void debug_printBytes(byte* a, int len)
{
  for(int i=0; i<len; i++) {
    PCss.print(a[i], HEX);
    PCss.print(' ');
  }
  PCss.println();
}
