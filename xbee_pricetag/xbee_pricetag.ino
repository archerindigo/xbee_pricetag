/*
 * The Chinese University of Hong Kong
 * CENG 3410 - Smart Hardware Design
 * Project: Smart Price Tags
 * 
 * Arduino Xbee Price Tag Controller
 * Author: Terry Tsang, William Wong
 * 
 * v0.2.1 (5/5/2017)
 */

#define DEBUG 0
#define HSU 0
#define OLED_RESET 4

#include <SoftwareSerial.h>
#include <PN532_I2C.h>
#include <PN532_HSU.h>
#include <PN532.h>
#include <NfcAdapter.h>
#include <ArduinoJson.h>
#include "simpleXbee.h"
#include "Adafruit_SSD1306.h"
#include "OLED.h"



// Global variables
#if DEBUG
SoftwareSerial PCss(10, 11);
#endif
RxPacket rx; // instance of RxPackage
Adafruit_SSD1306 Display(OLED_RESET);

#if HSU
PN532_HSU pn532_hsu(Serial1); // Use Serial1 HSU as NFC
NfcAdapter nfc = NfcAdapter(pn532_hsu);
#else
PN532_I2C pn532_i2c(Wire); // Use I2C as NFC
NfcAdapter nfc = NfcAdapter(pn532_i2c);
#endif


byte buff[80];
bool updateSignal = false;
float price = 1234.5;
char p_name[21] = "CENG3410 Price Tag";

void setup() {
  // put your setup code here, to run once:
  Display.begin(SSD1306_SWITCHCAPVCC, 0x3C);  // initialize with the I2C addr 0x3C
  OLED_display(); // Display default text
  Serial.begin(9600);
  #if DEBUG
  PCss.begin(9600);
  PCss.println("Start");
  #endif
  nfc.begin();
  #if DEBUG
  PCss.println("NFC initialized");
  #endif
  nfc.shutDown(); // Shutdown for power saving and avoid interference
}

void loop() {
  /* 
   *  1. Handle serial event
   */
  
  if (Serial.available()) {
    // got something from Xbee

    if (Serial.read() == 0x7E) {
      // got start of frame
      #if DEBUG
      PCss.println("Receiving frame");
      #endif
      rx = RxPacket(); // Reset packet instance

      // Read packet length
      Serial.readBytes(buff, 2);
      rx.setPackageLength(buff);
      #if DEBUG
      PCss.print("Length of packet: ");
      PCss.println(rx.getPackageLength());
      #endif

      // Read frame type
      byte frameType;
      Serial.readBytes(&frameType, 1);
      #if DEBUG
      PCss.print("Frame type: ");
      PCss.println(frameType, HEX);
      #endif
      if (frameType != 0x90) {
        // Invalid packet, reset and wait for next rx
        #if DEBUG
        PCss.println("Not a Rx packet");
        #endif
        rx = RxPacket(); // Reset packet instance
        return;
      }
      
      // Read 64-bit address
      Serial.readBytes(buff, 8);
      rx.setSA64(buff);
      #if DEBUG
      PCss.print("64-bit addr: ");
      debug_printBytes(rx.getSA64(), 8);
      #endif

      // Read 16-bit address
      Serial.readBytes(buff, 2);
      rx.setSA16(buff);
      #if DEBUG
      PCss.print("16-bit addr: ");
      debug_printBytes(rx.getSA16(), 2);
      #endif

      // Read receive option
      Serial.readBytes(buff, 1);
      rx.setRO(buff[0]);
      #if DEBUG
      PCss.print("RO: ");
      PCss.println(rx.getRO(), HEX);
      #endif
      
      // Read data
      Serial.readBytes(buff, rx.getDataLength());
      rx.setData(buff);
      #if DEBUG
      PCss.print("Payload(HEX): ");
      debug_printBytes(rx.getData(), rx.getDataLength());
      PCss.print("Payload(ASCII): ");
      PCss.println((char*)rx.getData());
      #endif

      // Read checksum and compare
      Serial.readBytes(buff, 1);
      rx.setChecksum(buff[0]);
      #if DEBUG
      PCss.print("Received Checksum: ");
      PCss.println(rx.getChecksum(), HEX);
      PCss.print("Calculated Checksum: ");
      PCss.println(rx.calcChecksum(), HEX);
      #endif
      if (rx.checkChecksum()) {
        #if DEBUG
        PCss.println("Checksum matched");
        #endif
        updateSignal = true; // Prepare to update tag
//        delay(100);  // Let serial print finish
      }
      else {
        #if DEBUG
        PCss.println("Checksum not matched, discarding packet");
        #endif
        rx = RxPacket();
      }
    }
  }

  /*
   * 2. Update tag
   */
  char JSONdata[60];
  strcpy(JSONdata, rx.getData());
  if (updateSignal) {
    updateSignal = 0;  // Reset signal
    Get_JSON(JSONdata);
    #if DEBUG
    PCss.print("p_name = ");
    PCss.println(p_name);
    PCss.print("price = ");
    PCss.println(price);
    PCss.println();
    #endif
    OLED_display();

    /*
     * 3. Write data to tag
     */
     
    int retry = 0;
    while (retry != 3)
    {
      #if DEBUG
      PCss.println("Writing NFC:");
      #endif
      if (nfc.tagPresent()) {
        NdefMessage message = NdefMessage();
        message.addUriRecord((char*)rx.getData());

        #if DEBUG
        PCss.println((char*)rx.getData());
        #endif
  
        if (nfc.write(message)) {
          #if DEBUG
          PCss.println("Tag written successfully");
          #endif
          retry = 3; // Done
        }
        else {
          #if DEBUG
          PCss.println("Tag write failed.");
          #endif
          retry++;
          delay(1000);
        }
      }
      else {
        // Timeout to find tag
        #if DEBUG
        PCss.println("Cannot find tag to write!");
        #endif
        retry++;
        //delay(1000);
      }
    }

    nfc.shutDown(); // Shutdown for power saving and avoid interference
  }
}

#if DEBUG
/*
 * Print byte array to PC
 */
void debug_printBytes(byte* a, int len)
{
  for(int i=0; i<len; i++) {
    PCss.print(a[i], HEX);
    PCss.print(' ');
  }
  PCss.println();
}
#endif

/*
 * Get_JSON()
 * Prasing received JSON and update p_name and price
 * input json[] will be altered so the RxPacket should be discarded
 * may copy the input json first but it consume more memory
 */
void Get_JSON(char json[]) {
//  PCss.print("json = ");
//  PCss.println(json);
  StaticJsonBuffer<200> jsonBuffer;
  
  JsonObject& product = jsonBuffer.parseObject(json);
  strcpy(p_name, product["p_name"]);
  price = product["price"];
}
