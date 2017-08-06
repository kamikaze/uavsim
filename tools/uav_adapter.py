#!/usr/bin/env python3
import argparse
import asyncio
import logging
import sys

from autobahn.wamp.types import RegisterOptions
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
from serial import Serial
from serial.serialutil import SerialException


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)

CROSSBAR_ROUTE = 'ws://127.0.0.1:8091/qgpsemu'

AP_CMD_ENGINE0_THROTTLE = 1
AP_CMD_ENGINE1_THROTTLE = 2

FG_COMMANDS = {
    AP_CMD_ENGINE0_THROTTLE: '/controls/engines/engine[0]/throttle {}',
    AP_CMD_ENGINE1_THROTTLE: '/controls/engines/engine[1]/throttle {}'
}

LAST_FG_COMMANDS = {}


class UAVAdapterComponent(ApplicationSession):
    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)
        self.serial_port = None

    async def connect_serial_port(self, path):
        while True:
            try:
                self.serial_port = Serial(path)
                logger.debug('Connected to serial port {}'.format(args.serial))

                break
            except SerialException:
                logger.warning('Error while opening serial port at {}'.format(args.serial))
                await asyncio.sleep(5)

    async def on_sim_nmea(self, nmea_sentence):
        logger.debug(nmea_sentence)

        try:
            self.serial_port.write('{}\n'.format(nmea_sentence).encode('utf-8'))
        except (AttributeError, SerialException):
            await self.connect_serial_port(self.config.extra['options'].serial)

    async def onJoin(self, details):
        await self.register(self, options=RegisterOptions(invoke='roundrobin'))

        await self.subscribe(self.on_sim_nmea, 'sim.nmea')

        try:
            await self.connect_serial_port(self.config.extra['options'].serial)

            while True:
                try:
                    if self.serial_port.in_waiting:
                        line = self.serial_port.readline().decode('utf-8').rstrip('\n')
                        self.publish('uav.cmd', line)

                    await asyncio.sleep(0.5)
                except (EOFError, ConnectionResetError, BrokenPipeError, KeyError, OSError, SerialException):
                    logger.warning('Error while reading from serial port')
                    await asyncio.sleep(5)
        finally:
            logger.debug('Closing serial port')
            if self.serial_port:
                self.serial_port.close()


def join_to_router(component_class, options):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    runner = ApplicationRunner(
        CROSSBAR_ROUTE,
        'qgpsemu',
        extra=options
    )

    rerun = True

    while rerun:
        rerun = False

        try:
            runner.run(component_class)
        # except gaierror:
        except OSError:
            # TODO: log about [Errno -3] Temporary failure in name resolution
            rerun = True


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

    args = parser.parse_args(sys.argv[1:])

    if not args.serial:
        logger.error('No comms method specified')
        exit(-1)

    join_to_router(UAVAdapterComponent, {'options': args})
