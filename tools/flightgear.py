#!/usr/bin/env python3
import logging
import re
import sys
from decimal import Decimal
from time import gmtime, strftime


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)


FG_PROP_REGEXP = re.compile('([^=]*)\s+=\s*\'([^\']*)\'\s*\(([^\r]*)\)')
TELNET_CONNECTION_RETRY_DELAY = 5

AP_CMD_ENGINE0_THROTTLE = 1
AP_CMD_ENGINE1_THROTTLE = 2

FG_COMMANDS = {
    AP_CMD_ENGINE0_THROTTLE: '/controls/engines/engine[0]/throttle {}',
    AP_CMD_ENGINE1_THROTTLE: '/controls/engines/engine[1]/throttle {}'
}

LAST_FG_COMMANDS = {}


def send_fg_command(telnet_client, line):
    cmd_id, *data = line.split(',')
    cmd_id = int(cmd_id)

    last_cmd = LAST_FG_COMMANDS.get(cmd_id)
    logger.info('{} {}'.format(cmd_id, last_cmd))

    if last_cmd == data:
        return

    cmd = FG_COMMANDS[cmd_id]
    cmd = 'set {}\r\n'.format(cmd.format(*data))
    logger.info(cmd)

    telnet_client.write(cmd.encode('ascii'))
    LAST_FG_COMMANDS[cmd_id] = data
    telnet_client.read_until(b'/> ')


def write_nmea(serial_port, line, verbose):
    if verbose:
        logger.info('Writing NMEA sentence: {}'.format(line))

    serial_port.write('{}\n'.format(line).encode('utf-8'))


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

    heading = telemetry['heading-deg']
    roll_x = telemetry['roll-deg']
    pitch_y = telemetry['pitch-deg']
    # yaw-deg is '' for some reason
    yaw_z = heading

    speed_over_ground = telemetry['groundspeed-kt']

    gpgga = '$GPGGA,{}.000,{:09.4f},{},{:010.4f},{},1,7,1.15,{},M,23.7,M,,*6F'.format(t, lat, lat_half, lon, lon_half, alt)
    gprmc = '$GPRMC,{}.000,A,{:09.4f},{},{:010.4f},{},{:.2f},267.70,{},,,A*6D'.format(t, lat, lat_half, lon, lon_half, speed_over_ground, d)
    exinj = '$EXINJ,{},{},{},{},NA'.format(heading, roll_x, pitch_y, yaw_z)

    return [gpgga, gprmc, exinj]


def read_fg_data(telnet_client, path):
    telnet_client.write('ls {}\r\n'.format(path).encode('ascii'))
    received_data = telnet_client.read_until(b'/> ').decode('ascii')
    telemetry = {}

    for row in received_data.split('\r\n')[:-1]:
        match = FG_PROP_REGEXP.match(row)

        if not match:
            continue

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
    telemetry.update(read_fg_data(telnet_client, 'orientation/model'))
    telemetry.update(read_fg_data(telnet_client, 'velocities'))

    return telemetry
