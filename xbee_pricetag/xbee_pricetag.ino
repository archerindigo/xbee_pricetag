/*
 * The Chinese University of Hong Kong
 * CENG 3410 - Smart Hardware Design
 * Project: Smart Price Tags
 * 
 * Arduino Xbee Price Tag Controller
 * Author: Terry Tsang
 * 
 * v0.1.0 (19/4/2017)
 */

#include <SoftwareSerial.h>
#include "include/simpleXbee.h"

SoftwareSerial PCss(9, 10);
RxPacket* rx = new RxPacket(); // instance of RxPackage
byte buff[100];

void setup() {
  // put your setup code here, to run once:
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
      PCss.print("Frame type: ");
      PCss.println(frameType, HEX);
      if (frameType != 0x90) {
        // Invalid packet, reset and wait for next rx
        PCss.println("Not a Rx packet");
        rx = new RxPacket(); // Reset packet instance
        return;
      }
      
      // Read 64-bit address
      Serial.readBytes(buff, 8);
      rx->setSA64(buff);
      PCss.print("Source 64-bit address: ");
      debug_printBytes(rx->getSA64(), 8);

      // Read 16-bit address
      Serial.readBytes(buff, 2);
      rx->setSA16(buff);
      PCss.print("Source 16-bit address: ");
      debug_printBytes(rx->getSA16(), 2);

      // Read receive option
      Serial.readBytes(buff, 1);
      rx->setRO(buff[0]);
      PCss.print("Receive option: ");
      PCss.println(rx->getRO(), HEX);
      
      // Read data
      Serial.readBytes(buff, 31);
      rx->setData(buff);
      PCss.print("Payload (HEX): ");
      debug_printBytes(rx->getData(), rx->getDataLength());
      PCss.print("Payload (ASCII): ");
      PCss.println((char*)rx->getData());

      // Read checksum and compare
      Serial.readBytes(buff, 1);
      rx->setChecksum(buff[0]);
      PCss.print("Received Checksum: ");
      PCss.println(rx->getChecksum(), HEX);
      PCss.print("Calculated Checksum: ");
      PCss.println(rx->calcChecksum(), HEX);
      if (rx->checkChecksum()) {
        PCss.println("Checksum matched");
      }
      else {
        PCss.println("Checksum not matched, discarding packet");
        rx = new RxPacket();
      }
    }
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

