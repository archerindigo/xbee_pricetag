#ifndef OLED
#define OLED

#if defined(ARDUINO) && ARDUINO >= 100
 #include "Arduino.h"
#else
 #include "WProgram.h"
#endif

void OLED_display();

void Get_JSON(char json[]);

String FloatToString(double val, int dec, int dig);

#endif
