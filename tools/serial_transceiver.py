#!/usr/bin/env python3

import argparse
import re
import sys
import telnetlib
from decimal import Decimal
from random import choice
from time import sleep, gmtime, strftime
from serial_port import SerialPort


FG_PROP_REGEXP = re.compile('([^=]*)\s+=\s*\'([^\']*)\'\s*\(([^\r]*)\)')


def write_nmea(serial_port, line, verbose):
    if verbose:
        print('Writing NMEA sentence: {}'.format(line))

    serial_port.write(line.encode('utf-8'))


def generate_nmea_sentences(telemetry):
    dt = gmtime()
    t = strftime('%H%M%S', dt)
    d = strftime('%d%m%y', dt)
    alt = Decimal(telemetry['altitude-ft']) * Decimal('0.3048')
    lat = telemetry['latitude-deg']
    lon = telemetry['longitude-deg']
    lat_half = 'N' if lat > 0 else 'S'
    lon_half = 'E' if lon > 0 else 'W'
    lat = lat*100 if lat > 0 else lat * -100
    lon = lon*100 if lon > 0 else lon * -100

    gpgga = '$GPGGA,{}.000,{:09.4f},{},{:010.4f},{},1,7,1.15,{},M,23.7,M,,*6F'.format(t, lat, lat_half, lon, lon_half, alt)
    gprmc = '$GPRMC,{}.000,A,{:09.4f},{},{:010.4f},{},0.03,267.70,{},,,A*6D'.format(t, lat, lat_half, lon, lon_half, d)
    exinj = '$EXINJ,{},NA'.format(telemetry['heading-deg'])

    print(gpgga)
    print(gprmc)
    print(exinj)

    return [gpgga, gprmc, exinj]


def read_telemetry(serial_port):
    if serial_port.any():
        serial_port.readline()


def read_fg_data(telnet_client, path):
    telnet_client.write('ls {}\r\n'.format(path).encode('ascii'))
    received_data = telnet_client.read_until(b'/> ').decode('ascii')
    telemetry = {}

    for row in received_data.split('\r\n')[:-1]:
        match = FG_PROP_REGEXP.match(row)

        if not match:
            continue

        # print(row)

        key, value, t = match.groups()

        if not value:
            continue

        if t == 'double':
            value = Decimal(value)
        elif t == 'bool':
            value = value == 'true'

        telemetry[key] = value

    return telemetry


def read_fg_telemetry(telnet_client):
    telemetry = read_fg_data(telnet_client, 'position')
    telemetry.update(read_fg_data(telnet_client, 'orientation'))

    return telemetry


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
        try:
            telemetry = read_fg_telemetry(telnet_client)
            nmea_sentences = generate_nmea_sentences(telemetry)

            for nmea_sentence in nmea_sentences:
                write_nmea(port, nmea_sentence, args.verbose)
                sleep(1)
        except (EOFError, ConnectionResetError, BrokenPipeError):
            sleep(5)

