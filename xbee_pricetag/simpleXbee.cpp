#include "simpleXbee.h"

RxPacket::RxPacket()
{
  
}

void RxPacket::setPackageLength(byte leng[]) 
{
  packageLength = (unsigned int)((leng[0] << 8) | leng[1]);
  dataLength = packageLength-12;
}

void RxPacket::setSA64(unsigned char SA[])
{
  memcpy(SA64, SA, 8);
}

void RxPacket::setSA16(unsigned char SA[]) 
{
  memcpy(SA16, SA, 2);
}

void RxPacket::setRO(byte option)
{
  RO = option;
}

void RxPacket::setChecksum(byte cs)
{
  checksum = cs;
}

/*
 * Read data from hardware serial port
 */
void RxPacket::setData(byte d[])
{
  memcpy(data, d, dataLength);
  data[dataLength] = '\0';
}

int RxPacket::getPackageLength()
{
  return packageLength;
}

int RxPacket::getDataLength()
{
  return dataLength;
}

byte* RxPacket::getSA16()
{
  return SA16;
}

byte* RxPacket::getSA64()
{
  return SA64;
}

byte RxPacket::getRO()
{
  return RO;
}

char* RxPacket::getData() 
{
  return data;
}

byte RxPacket::getChecksum()
{
  return checksum;
}

bool RxPacket::checkChecksum() {
  return checksum == calcChecksum();
}

byte RxPacket::calcChecksum()
{
  int cs = 0x90;
  int i;
  for(i=0; i<8; i++) {
    cs += SA64[i];
  }
  for(i=0; i<2; i++) {
    cs += SA16[i];
  }
  cs += RO;
  for(i=0; i<dataLength; i++) {
    cs += data[i];
  }

  return 0xFF - (byte)cs;
}
