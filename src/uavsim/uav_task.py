import asyncio
import logging
from serial import Serial
from serial.serialutil import SerialException

from uavsim.bus import bus

logger = logging.getLogger(__name__)


def _generate_nmea_sentences(telemetry: dict) -> list[str]:
    from time import gmtime, strftime
    from decimal import Decimal

    dt = gmtime()
    t = strftime('%H%M%S', dt)
    d = strftime('%d%m%y', dt)
    alt = Decimal(telemetry['altitude-ft']) * Decimal('0.3048')
    lat = telemetry['latitude-deg']
    lon = telemetry['longitude-deg']
    lat_half = 'N' if lat > 0 else 'S'
    lon_half = 'E' if lon > 0 else 'W'
    lat = lat * 100 if lat > 0 else lat * -100
    lon = lon * 100 if lon > 0 else lon * -100

    heading = telemetry['heading-deg']
    roll_x = telemetry['roll-deg']
    pitch_y = telemetry['pitch-deg']
    yaw_z = heading
    speed_over_ground = telemetry['groundspeed-kt']

    gpgga = f'$GPGGA,{t}.000,{lat:09.4f},{lat_half},{lon:010.4f},{lon_half},1,7,1.15,{alt},M,23.7,M,,*6F'
    gprmc = f'$GPRMC,{t}.000,A,{lat:09.4f},{lat_half},{lon:010.4f},{lon_half},{speed_over_ground:.2f},267.70,{d},,,A*6D'
    exinj = f'$EXINJ,{heading},{roll_x},{pitch_y},{yaw_z},NA'
    return [gpgga, gprmc, exinj]


async def run_uav(serial_path: str | None = None):
    sp: Serial | None = None

    async def ensure_serial() -> Serial | None:
        nonlocal sp
        if sp is None:
            if not serial_path:
                # No auto-detection for simplicity in this refactor; just skip if unspecified
                return None
            try:
                sp = Serial(serial_path)
                logger.info('Connected to serial port %s', serial_path)
            except SerialException:
                logger.warning('Unable to open serial port at %s', serial_path)
                sp = None
        return sp

    async def writer():
        q = bus.subscribe('map.pid')
        while True:
            kp, ki, kd = await q.get()
            s = await ensure_serial()
            if s:
                try:
                    s.write(f'$EXTPID,{kp},{ki},{kd},NA\n'.encode())
                except (AttributeError, SerialException):
                    sp.close() if sp else None
                    sp = None

    async def telemetry_to_nmea():
        q = bus.subscribe('sim.telemetry')
        while True:
            telemetry = await q.get()
            try:
                sentences = _generate_nmea_sentences(telemetry)
            except Exception as e:
                logger.debug('Failed to build NMEA: %s', e)
                continue
            s = await ensure_serial()
            if s:
                for nmea in sentences:
                    try:
                        s.write(f'{nmea}\n'.encode())
                    except (AttributeError, SerialException):
                        sp.close() if sp else None
                        sp = None

    async def reader():
        # Poll serial port and publish uav.cmd
        while True:
            if sp:
                try:
                    if sp.in_waiting:
                        line = sp.readline().decode('utf-8').rstrip('\n')
                        await bus.publish('uav.cmd', line)
                except (OSError, SerialException, UnicodeDecodeError):
                    try:
                        sp.close()
                    except Exception:
                        pass
                    sp = None
            await asyncio.sleep(0.5)

    # Start tasks
    asyncio.create_task(writer())
    asyncio.create_task(telemetry_to_nmea())
    await reader()
