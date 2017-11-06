#!/usr/bin/env python3
import argparse
import asyncio
import logging
import sys
from time import sleep

from autobahn import wamp
from autobahn.wamp.types import RegisterOptions
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner

from uavsim import flightgear
from uavsim.flightgear.client import AbstractClient, TelnetClient, UDPClient

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

CROSSBAR_ROUTE = 'ws://127.0.0.1:8091/uavsim'
FG_CONNECTION_RETRY_DELAY = 5


class SimCommanderComponent(ApplicationSession):
    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)
        self.client: AbstractClient = self.config.extra['client']
        self.is_running: bool = False

    # @wamp.subscribe('uav.cmd')
    async def on_uav_cmd(self, line):
        logger.debug(line)
        self.client.send_command(line)

    async def on_map_position_force(self, lat, lon):
        logger.debug('Position forced: {}, {}'.format(lat, lon))
        self.client.set_position(lat, lon)

    async def onJoin(self, details):
        await self.register(self, options=RegisterOptions(invoke='roundrobin'))

        await self.subscribe(self.on_uav_cmd, 'uav.cmd')
        await self.subscribe(self.on_map_position_force, 'map.position')

        self.is_running = True

        while self.is_running:
            try:
                telemetry = flightgear.read_fg_telemetry(self.config.extra['client'])

                self.publish('sim.telemetry', telemetry)

                await asyncio.sleep(0.25)
            except (EOFError, ConnectionResetError, BrokenPipeError, KeyError):
                await asyncio.sleep(5)


def join_to_router(component_class, options):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    runner = ApplicationRunner(
        CROSSBAR_ROUTE,
        'uavsim',
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
        description='FlightGear adapter',
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
        default=None
    )
    parser.add_argument(
        '--telnet-port',
        dest='telnet_port',
        help='Telnet port',
        type=int,
        default=5401
    )
    parser.add_argument(
        '--udp-out-host',
        dest='udp_out_host',
        help='FlightGear UDP-out host',
        default=None
    )
    parser.add_argument(
        '--udp-out-port',
        dest='udp_out_port',
        help='FlightGear UDP-out port',
        type=int,
        default=5500
    )
    parser.add_argument(
        '--udp-in-host',
        dest='udp_in_host',
        help='FlightGear UDP-in host',
        default=None
    )
    parser.add_argument(
        '--udp-in-port',
        dest='udp_in_port',
        help='FlightGear UDP-in port',
        type=int,
        default=5501
    )

    args = parser.parse_args(sys.argv[1:])
    fg_client: AbstractClient = None

    if args.telnet_host:
        fg_client = TelnetClient(args.telnet_host, args.telnet_port)
    elif args.udp_out_host:
        fg_client = UDPClient(args.udp_out_host, args.udp_out_port)

    if fg_client:
        while True:
            try:
                fg_client.connect()

                break
            except ConnectionRefusedError:
                logger.warning('Connection to {}:{} failed, retrying after {}s'.format(fg_client.host,
                                                                                       fg_client.port,
                                                                                       FG_CONNECTION_RETRY_DELAY)
                               )
                sleep(FG_CONNECTION_RETRY_DELAY)

        logger.debug('Connected to FG')
        join_to_router(SimCommanderComponent, {'client': fg_client})
    else:
        logger.critical('Unable to initialize FG client')
