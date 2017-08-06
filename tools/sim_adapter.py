#!/usr/bin/env python3
import argparse
import asyncio
import logging
import sys
import telnetlib
from time import sleep

from autobahn import wamp
from autobahn.wamp.types import RegisterOptions
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner

import flightgear


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)

CROSSBAR_ROUTE = 'ws://127.0.0.1:8091/qgpsemu'
TELNET_CONNECTION_RETRY_DELAY = 5


class SimCommanderComponent(ApplicationSession):
    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)
        self.is_running = False

    # @wamp.subscribe('uav.cmd')
    async def on_uav_cmd(self, line):
        logger.debug(line)
        flightgear.send_fg_command(self.config.extra['client'], line)

    async def onJoin(self, details):
        await self.register(self, options=RegisterOptions(invoke='roundrobin'))

        await self.subscribe(self.on_uav_cmd, 'uav.cmd')

        self.is_running = True

        while self.is_running:
            try:
                telemetry = flightgear.read_fg_telemetry(telnet_client)
                nmea_sentences = flightgear.generate_nmea_sentences(telemetry)

                for nmea_sentence in nmea_sentences:
                    self.publish('sim.nmea', nmea_sentence)

                await asyncio.sleep(0.25)
            except (EOFError, ConnectionResetError, BrokenPipeError, KeyError):
                await asyncio.sleep(5)


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
        description='NMEA sender and telemetry receiver',
    )
    parser.add_argument(
        '-v', '--verbose',
        dest='verbose',
        action='store_true',
        help='Turn on verbose messages',
        default=False
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
        type=int,
        default=5401
    )

    args = parser.parse_args(sys.argv[1:])

    while True:
        try:
            telnet_client = telnetlib.Telnet(host=args.telnet_host, port=args.telnet_port)
            logger.debug('Connected to FG')

            break
        except ConnectionRefusedError:
            logger.warning('Telnet connection to {}:{} failed, retrying after {}s'.format(args.telnet_host,
                                                                                          args.telnet_port,
                                                                                          TELNET_CONNECTION_RETRY_DELAY)
                           )
            sleep(TELNET_CONNECTION_RETRY_DELAY)

    join_to_router(SimCommanderComponent, {'client': telnet_client})
