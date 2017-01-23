#!/usr/bin/env python3

import argparse
import sys
import telnetlib
from random import choice
from time import sleep
from serial_port import SerialPort


NMEA_TEST_LINES = [
    '$GPGGA,192917.000,5654.7984,N,02410.9481,E,1,7,1.15,12.2,M,23.7,M,,*6F',
    '$GPGGA,192322.000,5654.7977,N,02410.9479,E,1,8,1.02,11.9,M,23.7,M,,*69',
    '$GPGGA,191945.000,5654.7968,N,02410.9479,E,1,9,0.91,11.1,M,23.7,M,,*6D',
    '$GPGGA,191636.000,5654.7967,N,02410.9484,E,1,9,0.92,10.8,M,23.7,M,,*60',
    '$GPGGA,191301.000,5654.8017,N,02410.9511,E,1,8,1.13,26.5,M,23.7,M,,*6C'
]

def write_nmea(serial_port, line, verbose):
    if verbose:
        print('Writing NMEA sentence: {}'.format(line))

    serial_port.write(line.encode('utf-8'))


def read_telemetry(serial_port):
    if serial_port.any():
        serial_port.readline()


def read_fg_telemetry(telnet_client):
    telnet_client.write(b'ls position\r\n')
    position = telnet_client.read_until(b'/> ').decode('ascii')
    print(position)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='NMEA sender and telemetry receiver via serial port',
    )
    parser.add_argument(
        '-v', '--verbose',
        dest='verbose',
        action='store_true',
        help='Turn on verbose messages',
        default=False
    )
    parser.add_argument(
        '--serial',
        dest='serial',
        help='Send data over a serial port',
        default=None
    )
    parser.add_argument(
        '--telnet-host',
        dest='telnet_host',
        help='Telnet host',
        default='127.0.0.1'
    )
    parser.add_argument(
        '--telnet-port',
        dest='telnet_port',
        help='Telnet port',
        default=5401
    )

    args = parser.parse_args(sys.argv[1:])

    if args.serial:
        port = SerialPort(args.serial)
    else:
        print('No comms method specified')
        exit(-1)

    telnet_client = telnetlib.Telnet(host=args.telnet_host, port=int(args.telnet_port))

    while True:
        read_fg_telemetry(telnet_client)
        write_nmea(port, choice(NMEA_TEST_LINES), args.verbose)
        sleep(1)

