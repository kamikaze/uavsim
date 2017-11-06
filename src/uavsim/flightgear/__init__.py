#!/usr/bin/env python3
import logging
import sys

import datetime

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)

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


def read_fg_telemetry(telnet_client):
    telemetry = {'dt': datetime.datetime.utcnow().timestamp()}
    telemetry.update(telnet_client.read_fg_data('position'))
    telemetry.update(telnet_client.read_fg_data('orientation/model'))
    telemetry.update(telnet_client.read_fg_data('velocities'))

    return telemetry
