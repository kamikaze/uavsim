import argparse
import asyncio
import logging
import os
import sys
from time import gmtime, strftime, sleep

import pyudev
from autobahn.wamp.types import RegisterOptions
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
from decimal import Decimal

from serial import Serial
from serial.serialutil import SerialException


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)

CROSSBAR_ROUTE = 'ws://127.0.0.1:8091/uavsim'


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

    gpgga = '$GPGGA,{}.000,{:09.4f},{},{:010.4f},{},1,7,1.15,{},M,23.7,M,,*6F'.format(
        t, lat, lat_half, lon, lon_half, alt)
    gprmc = '$GPRMC,{}.000,A,{:09.4f},{},{:010.4f},{},{:.2f},267.70,{},,,A*6D'.format(
        t, lat, lat_half, lon, lon_half, speed_over_ground, d)
    exinj = '$EXINJ,{},{},{},{},NA'.format(heading, roll_x, pitch_y, yaw_z)

    return [gpgga, gprmc, exinj]


class UAVAdapterComponent(ApplicationSession):
    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)
        self.serial_port = None

    @staticmethod
    def _detect_device_path():
        context = pyudev.Context()
        devices = context.list_devices(subsystem='usb', driver='cdc_acm', PRODUCT='f055/9800/200')

        for device in devices:
            if device.properties.get('INTERFACE') == '2/2/1':
                break
        else:
            device = None

        if device is None:
            logger.info('No device found, waiting for it')
            monitor = pyudev.Monitor.from_netlink(context)
            monitor.filter_by(subsystem='usb')

            for device in iter(monitor.poll, None):
                if device.action == 'add':
                    if device.properties['PRODUCT'] == 'f055/9800/200' and device.properties.get('INTERFACE') == '2/2/1':
                        break

        device_filename = os.listdir(f'{device.sys_path}/tty/')[0]

        return f'/dev/{device_filename}'

    async def connect_serial_port(self, path=None):
        if self.serial_port:
            self.serial_port.close()
            self.serial_port = None

        if not path:
            logger.info('Looking for a device')
            path = self._detect_device_path()

        try:
            await asyncio.sleep(1)
            self.serial_port = Serial(path)
            logger.info('Connected to serial port {}'.format(path))
        except SerialException:
            logger.warning('Error while opening serial port at {}'.format(path))
            await asyncio.sleep(5)

    async def send_nmea_sentence_to_uav(self, nmea_sentence):
        logger.debug(nmea_sentence)

        if self.serial_port:
            try:
                self.serial_port.write('{}\n'.format(nmea_sentence).encode('utf-8'))
            except (AttributeError, SerialException):
                await self.connect_serial_port(self.config.extra['options'].serial)

    async def on_sim_telemetry(self, telemetry):
        nmea_sentences = generate_nmea_sentences(telemetry)

        for nmea_sentence in nmea_sentences:
            await self.send_nmea_sentence_to_uav(nmea_sentence)

    async def on_map_pid_force(self, kp, ki, kd):
        await self.send_nmea_sentence_to_uav(f'$EXTPID,{kp},{ki},{kd},NA')

    async def onJoin(self, details):
        await self.register(self, options=RegisterOptions(invoke='roundrobin'))

        await self.subscribe(self.on_sim_telemetry, 'sim.telemetry')
        await self.subscribe(self.on_map_pid_force, 'map.pid')

        try:
            await self.connect_serial_port(self.config.extra['options'].serial)

            while True:
                try:
                    if self.serial_port:
                        if self.serial_port.in_waiting:
                            line = self.serial_port.readline().decode('utf-8').rstrip('\n')
                            self.publish('uav.cmd', line)

                    await asyncio.sleep(0.5)
                except (EOFError, ConnectionResetError, BrokenPipeError, KeyError, OSError, SerialException):
                    logger.error('Connection with serial port failed, reconnecting...')
                    await self.connect_serial_port(self.config.extra['options'].serial)
        finally:
            logger.debug('Closing serial port')
            if self.serial_port:
                self.serial_port.close()
                del self.serial_port


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
        description='UAV adapter',
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

    sleep(5)

    join_to_router(UAVAdapterComponent, {'options': args})
