#!/usr/bin/env python3
#
# led-485_setuptool A tool to communicate via rs485 modbus with the LED-485 displays
#

import argparse
import sys
import struct
import pymodbus.client as modbus_client


def connect(args, new_baudrate=None):
    """Connect to serial port or modbus gateway"""
    if args.host:
        # Modbus gateway
        client = modbus_client.ModbusTcpClient(args.host,
                                               port=args.tcp_port,
                                               timeout=args.timeout,
                                               retries=3)

    elif args.serial_port:
        # Serial rs485 port
        if new_baudrate:
            baudrate = new_baudrate
        else:
            baudrate = args.baudrate
        client = modbus_client.ModbusSerialClient(port=args.serial_port,
                                                  timeout=args.timeout,
                                                  baudrate=baudrate,
                                                  bytesize=8,
                                                  parity='N',
                                                  stopbits=1)
    else:
        print('Neither a serial port nor a host has been defined. '
              'I can not work like this!!\nExiting!', file=sys.stderr)
        sys.exit(1)

    return client


def address_limit(address):
    """ Type function for argparse - an int within some predefined bounds """
    try:
        address = int(address)
    except ValueError:
        raise argparse.ArgumentTypeError('Must be an integer')
    min_val = 1
    max_val = 255
    if address < min_val or address > max_val:
        raise argparse.ArgumentTypeError('Argument must be < ' + str(min_val) + 'and > ' + str(max_val))
    return address


def i16_limit(string):
    """ Type function for argparse - an int bounds for signed 16-bit integer """
    value = int(string)
    if not -2 ** 15 < value < 2 ** 15 - 1:
        raise argparse.ArgumentTypeError('Must be an integer in the range -32768 to 32767')
    return value


def ieee754(value_list):
    """Convert the value list as IEEE 754 32 bit single precision floats from the electricity meters"""
    bin_float = format(value_list[0] & 0xffff, '016b') + format(value_list[1] & 0xffff, '016b')
    packed_v = struct.pack('>L', int(bin_float, 2))
    return struct.unpack('>f', packed_v)[0]


def reverse_ieee754(float_value):
    """Convert a float to an IEEE 754 32 bit single precision value list"""
    # Pack the float as a 32-bit unsigned long (big-endian)
    packed_v = struct.pack('>f', float_value)
    # Unpack as a 32-bit unsigned long (big-endian) and convert to binary
    bin_value = format(struct.unpack('>L', packed_v)[0], '032b')
    # Split the binary string into two 16-bit parts and convert them to integers
    value1 = int(bin_value[:16], 2)
    value2 = int(bin_value[16:], 2)
    return [value1, value2]


def i16(value):
    if value < 0:
        value += 2**16
    return value


def u16(value):
    return value


def modbus_req(args, register_name, client=None, payload=None, unit_id=None):
    """Read or write to a register from a display"""
    assert type(register_name) is str
    if not client:
        client = connect(args)
    if not unit_id:
        unit_id = args.unit_id

    display_regs = {
            'LED-485': {
                'i16': [6, 0x0, 1, '16-bit signed integer (see also the decimal point setting)', 'I16'],
                'dec_point': [6, 0x4, 1, 'Position of decimalpoint', 'U16'],
                'set_unit_id': [6, 0x2, 1, 'Set new unit id ("modbus address")', 'U16'],
                'set_baudrate': [6, 0x3, 1, 'Set new baudrate', 'U16'],
                'float': [16, 0x90, 2, 'float', 'F32'],
                'str_custom_segment': [16, 0x80, 'n/a', 'custom segment string', ''],
                'str_ascii': [16, 0x70, 'n/a', 'ASCII string', ''],
                },
    }

    # Function code, hex address, count/length of registers to read (multiple of 2 bytes, i.e. 2=4bytes),
    # info text (e.g. unit), response type (how to interpret the response)
    dregs = display_regs['LED-485']
    if register_name not in dregs:
        info_text = 'Not supported for this model'
        value = None
    else:
        function_code, address, count, info_text, data_type = dregs[register_name]
        if function_code in [6, 16]:
            if payload is None:
                print(f'ERROR missing payload for {register_name}\nExiting!', sys.stderr)
                sys.exit(1)
            if data_type:
                if data_type == 'F32':
                    payload = reverse_ieee754(payload)
                elif data_type == 'U16':
                    payload = u16(payload)
                elif data_type == 'I16':
                    payload = i16(payload)
                elif data_type == '':
                    pass
                else:
                    print(f'ERROR data type for {register_name} using function code {function_code} is not supported. '
                          f'Please check the script.\nExiting!', sys.stderr)
                    sys.exit(1)
            if function_code == 6:
                res = client.write_register(address, payload, unit_id)
            elif function_code == 16:
                res = client.write_registers(address, payload, unit_id)
        else:
            print('ERROR: Unsupported function code. This should not be happening '
                  '(check that all function codes are supported in the script).\nExiting!', file=sys.stderr)
            sys.exit(1)
        if res.isError():
            print(f'ERROR: We got an error back when requesting {register_name}:')
            if hasattr(res, 'encode'):
                print('res.encode(): %s' % res.encode())
            if hasattr(res, 'function_code'):
                print("Function code: %s" % res.function_code)
            if hasattr(res, 'string'):
                print("Error string: %s" % res.string)
            print('Exiting!')
            sys.exit(1)
        regs = res.registers
        if regs:
            if data_type == 'F16':
                value = ieee754(regs)
            elif data_type == 'U16':
                value = u16(regs)
            elif data_type == 'I16':
                value = i16(regs)
            elif data_type == '':
                value = None
            else:
                print('ERROR: Response type not supported. This should not be happening '
                      '(check that all response types are supported in the script).\nExiting!', file=sys.stderr)
                sys.exit(1)
        else:
            value = None
    return {'value': value, 'info_text': info_text}


def display_i16(args, client=None):
    """Display a signed int on the display. See also display_dec_point()"""
    value = int(args.value)
    print(f'Display: "{value}" ', end='')
    response = modbus_req(args, 'i16', payload=value, client=client)
    print(response['info_text'])


def display_dec_point(args, client=None):
    """Change the configured decimal point for the meter. The setting is lost upon a reboot of the display."""
    value = int(args.decimal_point)
    print(f'Display: "{value}" ', end='')
    response = modbus_req(args, 'dec_point', payload=value, client=client)
    print(response['info_text'])


def display_float(args, client=None):
    """Display a float"""
    value = float(args.float)
    print(f'Display: "{value}" ', end='')
    response = modbus_req(args, 'float', payload=value, client=client)
    print(response['info_text'])


def display_cust_seg(args, client=None, string=None):
    """Display a string using the Custom Segment method"""
    # Input validation
    if not 1 <= len(string) <= args.display_size or not type(string) is str:
        print('ERROR the provided string is not between 1 and 6 characters long or it is not a string.\nExiting!',
              file=sys.stderr)
        sys.exit(1)
    string = string.upper()
    string = string.replace('_', ' ')
    for char in string:
        oc = ord(char)
        if not (oc == 32 or 48 <= oc <= 57 or 65 <= oc <= 90):
            print('ERROR only space, A-Z and 0-9 characters are allowed.\nExiting!', file=sys.stderr)
            sys.exit(1)
    map_tbl = {
        ' ': '00', '0': '3f', '1': '06', '2': '5b', '3': '4f',
        '4': '66', '5': '6d', '6': '7d', '7': '07', '8': '7f',
        '9': '6f', 'A': '77', 'B': '7c', 'C': '39', 'D': '5e',
        'E': '79', 'F': '71', 'G': '3d', 'H': '76', 'I': '10',
        'J': '0e', 'K': '7a', 'L': '38', 'M': '55', 'N': '54',
        'O': '5c', 'P': '73', 'Q': '67', 'R': '50', 'S': '64',
        'T': '78', 'U': '3e', 'V': '62', 'W': '6a', 'X': '36',
        'Y': '6e', 'Z': '49',
    }

    if len(string) % 2 == 1:
        string += ' '
    payload = []
    for i in range(len(string)//2):
        hex_str = ''
        for j in range(2):
            hex_str += map_tbl[string[i*2+j]]
        payload.append(int(hex_str, 16))
    print(f'Display: "{string}" ', end='')
    print(payload)
    response = modbus_req(args, 'str_custom_segment', payload=payload, client=client)
    print(response['info_text'])


def display_ascii(args, client=None, string=None):
    """Display an ASCII string"""
    # Input validation
    if not 1 <= len(string) <= args.display_size or not type(string) is str:
        print('ERROR the provided string is not between 1 and 6 characters long or it is not a string.\nExiting!',
              file=sys.stderr)
        sys.exit(1)
    string = string.rjust(args.display_size)
    payload = []
    if len(string) % 2 == 1:
        string += ' '
    i = 0
    prev = 0
    for char in string:
        oc = ord(char)
        # not all ASCII characters are allowed. The ones below worked on the display I tested with.
        if not (0x20 <= oc <= 0x7E):
            print(f'ERROR character "{char}" is not allowed\nExiting!', file=sys.stderr)
            sys.exit(1)
        if i % 2 == 0:
            prev = oc
        else:
            # We need to convert to uint16
            payload.append(prev*2**8+oc)
        i += 1
    print(f'Display: "{string}" ', end='')
    response = modbus_req(args, 'str_ascii', payload=payload, client=client)
    print(response['info_text'])


def set_baudrate(args, client=None):
    """Change the configured baudrate of the display"""
    baudrate_dict = {1: 1200, 2: 2400, 3: 4800, 4: 9600, 5: 19200, 6: 38400, 7: 57600, 8: 115200}
    # Set the new baudrate
    baudrate = list(baudrate_dict.keys())[list(baudrate_dict.values()).index(int(args.set_baudrate))]
    print(f'Setting the baudrate to {args.set_baudrate}')
    reading = modbus_req(args, 'set_baudrate', payload=baudrate, client=client)


def set_unit_id(args, client=None):
    """Change the configured unit id for the display"""
    # Set the new baudrate
    new_value = int(args.set_unit_id)
    print(f'Setting the unit id ("modbus address") to {new_value}')
    reading = modbus_req(args, 'set_unit_id', payload=new_value, client=client)


def main():
    """ The main function """
    # Argument parsing
    parser = argparse.ArgumentParser(prog='LED-485_setuptool.py',
                                     description='A tool to communicate via rs485 modbus with the LED-485 displays')
    ch_group = parser.add_mutually_exclusive_group()
    dev_group = parser.add_mutually_exclusive_group()
    display_group = parser.add_mutually_exclusive_group()
    dev_group.add_argument('-p', '--serial-port', help='Serial port')
    dev_group.add_argument('--host', help='Hostname (if modbus gateway)')
    parser.add_argument('-b', '--baudrate', help='Baudrate (when using a serial port)',
                        default=9600, type=int)
    ch_group.add_argument('--set-baudrate', help='Set the serial baudrate',
                          choices=['1200', '2400', '4800', '9600', '19200', '38400', '57600', '115200'])
    parser.add_argument('--tcp-port', help='Modbus gateway TCP port', default=502, type=int)
    parser.add_argument('-u', '--unit-id',
                        help='Modbus unit id to use (1-255). This is the "slave id" or "address" of the modbus slave',
                        default='1', type=address_limit)
    ch_group.add_argument('--set-unit-id', help='Set modbus unit id (1-255)', type=address_limit, )
    parser.add_argument('-t', '--timeout', help='Timeout in seconds', default=2, type=int)
    parser.add_argument('-d', '--display-size', help='Number of 7-segment elements in the display.',
                        default=6, type=int, choices=[4, 5, 6])
    display_group.add_argument('--value', help='Show a 16-bit signed integer in the display',
                               type=i16_limit)
    display_group.add_argument('--decimal-point', help='Decimal point', choices=['0', '1', '2', '3'])
    display_group.add_argument('--cust-seg', help='Write a simple string using the "custom segment" '
                                                  'method. (_ is space), 0-9, A-Z', type=str)
    display_group.add_argument('--str', help='Write an ASCII string', type=str)

    # # For some reason the display does not work with this documented feature, so I am outcommenting it for now
    # display_group.add_argument('--float', help='Display a float')

    args = parser.parse_args()

    print('Starting the LED-485 setuptool programm')

    # Connect
    client = connect(args)

    if args.set_baudrate:
        set_baudrate(args, client=client)

    if args.set_unit_id:
        set_unit_id(args, client=client)

    if args.value is not None:
        display_i16(args, client=client)

    if args.decimal_point:
        display_dec_point(args, client=client)

    if args.cust_seg:
        display_cust_seg(args, client=client, string=args.cust_seg)

    if args.str:
        display_ascii(args, client=client, string=args.str)

    # # For some reason the display does not work with this documented feature, so I am outcommenting it for now
    # if args.float:
    #     display_float(args, client=client)


if __name__ == '__main__':
    main()
