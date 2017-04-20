#ifndef SIMPLE_XBEE
#define SIMPLE_XBEE

#if defined(ARDUINO) && ARDUINO >= 100
  #include "Arduino.h"
#else
  #include "WProgram.h"
#endif

class RxPacket
{
  private:
    int packageLength;  // length of packet
    int dataLength;
    byte SA64[8];  // 64-bit address
    byte SA16[2];  // 16-bit address
    byte RO; // receive option
    char data[60];
    byte checksum;
    
  public:
    RxPacket();
    void setPackageLength(byte leng[]);
    void setSA64(unsigned char SA[]);
    void setSA16(unsigned char SA[]);
    void setRO(byte option);
    void setChecksum(byte cs);
    void setData(byte d[]);

    int getPackageLength();
    int getDataLength();
    byte* getSA16();
    byte* getSA64();
    byte getRO();
    char* getData();
    byte getChecksum();
    bool checkChecksum();
    byte calcChecksum();
};

#endif
