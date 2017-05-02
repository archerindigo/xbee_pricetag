#### The Chinese University of Hong Kong
#### CENG3410 Final Project
#### Spring 2017
## Smart Price Tags
This project aims to build an Zigbee network for electronic price tags

The following features will be provided:
1. Remote price tag update from PC program
2. Android app for recording purchased items by tapping on the NFC tag of the price tag

Group members:
- Terry Tsang
- William Wong
- Alan Chan
- Alison Wong

### Update Notes for Arduino controller (xbee_pricetag)
**v0.1.1 (21/4/2017)**
[Bug fix]
- Resolved memory leak by ArduinoJSON and RxPacket

[Miscellaneous]
- Provided switch of debug message on software serial pin 9, 10

[Known issues]
- Insufficient memory on Arduino Uno. Should migrate to Arduino Mega in the future
- Funduino Xbee shield routes XBee's UART to Arduino pin 0 and 1 only which make UART NFC module unable to be used on Arduino UNO, which has only 1 UART

**v0.1.0 (19/4/2017)**
[New features]
- Receiving Zigbee Rx packet from hardware UART
- Update display according to received packet

[Known issues]
- Memory leak occurs when using ArduinoJSON libraray to prase data
- High memory usage by ArduinoJSON and Adafruit_SSD1306 OLED driver

### Update Notes for Console Program (xbee_pricetag_console)
**v0.1.1 (2/5/2017)**
[New features]
- Increase/Decrease all prices by 10%

[Known issues]
- Coordinator may not response in time when tramitting a frame to a non-exist address, leading to synchronzation miss. Should wait for transmit status frame after sending each frame.

**v0.1.0 (2/5/2017)**
- First version with all basic function implemented (Expect increse/decrease all price)