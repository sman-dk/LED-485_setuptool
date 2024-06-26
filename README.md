# LED-485_setuptool
Change modbus settings and write text etc. on RS485 displays e.g. LED-485-046 and LED-046

The displays should be waterproof and may be found on chinese websites like Ali Express etc.

![LED-485-046 display showing the text "HELLO"](pictures/LED-485-046_hello.jpg)

![LED-485-046 display showing 12.345](pictures/LED-485-046_12345.jpg)

![Backside of the LED-485-046 display](pictures/LED-485-046_backside.jpg)

![LED-046 showing the string "Github"](pictures/LED-046_Github.jpg)

## Features
- Write a simple text string (' ', 0-9, A-Z)
- Write a number (integer or decimal/float) in the display
- Change baudrate and modbus unit id ("modbus address")

Both a serial device (e.g. USB RS485 adaptor) and modbus gateway is supported.

## Supported models
There are a number of different models (listed here for reference).

Feel free to send me a display for me to test on.

### Tested
- LED-485-046: 6-digit red
- LED-485-046: 6-digit blue*
- LED-046: 6-digit red**

*) I only really tested the red one of the same model, but it is listed here because of the type and size of the display are the parameters that matter :)
**) --cust-seg will not work with this display, but since --str works there is no loss of display features

### Untested
- LED-485-083: 3-digit red
- LED-485-054: 4-digit red
- LED-485-055: 5-digit red
- LED-485-083: 3-digit blue
- LED-485-054: 4-digit blue
- LED-485-055: 5-digit blue

## Notes
The display ships from the manufacturer with modbus unit id ("modbus address") 1 and baudrate 9600 8N1

## Dependencies

```pip3 install pymodbus pyserial```

## Usage
```commandline
$ ./led-485_setuptool.py -h
usage: LED-485_setuptool.py [-h] [-p SERIAL_PORT | --host HOST] [-b BAUDRATE] [--set-baudrate {1200,2400,4800,9600,19200,38400,57600,115200}] [--tcp-port TCP_PORT] [-u UNIT_ID] [--set-unit-id SET_UNIT_ID] [-t TIMEOUT] [-d {4,5,6}]
                            [--value VALUE | --decimal-point {0,1,2,3} | --cust-seg CUST_SEG | --str STR]

A tool to communicate via rs485 modbus with the LED-485 displays

options:
  -h, --help            show this help message and exit
  -p SERIAL_PORT, --serial-port SERIAL_PORT
                        Serial port
  --host HOST           Hostname (if modbus gateway)
  -b BAUDRATE, --baudrate BAUDRATE
                        Baudrate (when using a serial port)
  --set-baudrate {1200,2400,4800,9600,19200,38400,57600,115200}
                        Set the serial baudrate
  --tcp-port TCP_PORT   Modbus gateway TCP port
  -u UNIT_ID, --unit-id UNIT_ID
                        Modbus unit id to use (1-255). This is the "slave id" or "address" of the modbus slave
  --set-unit-id SET_UNIT_ID
                        Set modbus unit id (1-255)
  -t TIMEOUT, --timeout TIMEOUT
                        Timeout in seconds
  -d {4,5,6}, --display-size {4,5,6}
                        Number of 7-segment elements in the display.
  --value VALUE         Show a 16-bit signed integer in the display
  --decimal-point {0,1,2,3}
                        Decimal point
  --cust-seg CUST_SEG   Write a simple string using the "custom segment" method. (_ is space), 0-9, A-Z
  --str STR             Write an ASCII string
```
## Examples
Display an ASCII string:
```
$ ./led-485_setuptool.py --serial-port /dev/ttyUSB0 --str Github
Starting the LED-485 setuptool programm
Display: "Github" ASCII string
```

Display the value 12.345:
```
$ ./led-485_setuptool.py --serial-port /dev/ttyUSB0 --decimal-point 3
Starting the LED-485 setuptool programm
Display: "3" Position of decimalpoint
```
(decimal point is saved until the display looses power)
```
$ ./led-485_setuptool.py --serial-port /dev/ttyUSB0 --value 12345
Starting the LED-485 setuptool programm
Display: "12345" 16-bit signed integer (see also the decimal point setting)
```

Or you can just show it as a string:
```
$ ./led-485_setuptool.py --serial-port /dev/ttyUSB0 --str 12.345
Starting the LED-485 setuptool programm
Display: "12.345" ASCII string
```

Change the baudrate from 9600 to 19200:
```
$ ./led-485_setuptool.py --serial-port /dev/ttyUSB0  --baudrate 9600 --set-baudrate 19200
Starting the LED-485 setuptool programm
Setting the baudrate to 19200
```

Change the unit id from 1 to 5 (unit id is also sometimes referred to as "modbus address" or "slave id")
```
$ ./led-485_setuptool.py --serial-port /dev/ttyUSB0 --unit-id 1 --set-unit-id 5
Starting the LED-485 setuptool programm
Setting the unit id ("modbus address") to 5
```
