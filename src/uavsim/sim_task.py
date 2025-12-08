import asyncio
import logging
from time import sleep

from uavsim import flightgear
from uavsim.bus import bus
from uavsim.flightgear.client import TelnetClient, UDPClient, AbstractClient

logger = logging.getLogger(__name__)


async def _forward_uav_cmd(client: AbstractClient):
    q = bus.subscribe('uav.cmd')
    while True:
        line = await q.get()
        try:
            client.send_command(line)
        except Exception as e:
            logger.debug('send_command failed: %s', e)


async def _forward_map_position(client: AbstractClient):
    q = bus.subscribe('map.position')
    while True:
        lat, lon = await q.get()
        try:
            client.set_position(lat, lon)
        except Exception as e:
            logger.debug('set_position failed: %s', e)


async def run_sim(telnet_host: str | None = '127.0.0.1', telnet_port: int = 5901,
                  udp_out_host: str | None = None, udp_out_port: int = 5500) -> None:
    # Initialize FlightGear client (prefer telnet if host provided)
    client: AbstractClient | None = None
    if telnet_host:
        client = TelnetClient(telnet_host, telnet_port)
    elif udp_out_host:
        client = UDPClient(udp_out_host, udp_out_port)

    if client is None:
        logger.error('No FlightGear client configured')
        return

    # Connect with retries (blocking sleep acceptable during startup)
    while True:
        try:
            client.connect()
            break
        except ConnectionRefusedError:
            logger.warning('Connection to %s:%s failed, retrying in 5s', client.host, client.port)
            sleep(5)

    # Start forwarding tasks
    asyncio.create_task(_forward_uav_cmd(client))
    asyncio.create_task(_forward_map_position(client))

    # Telemetry loop
    while True:
        try:
            telemetry = flightgear.read_fg_telemetry(client)
            await bus.publish('sim.telemetry', telemetry)
            await asyncio.sleep(0.25)
        except (EOFError, ConnectionResetError, BrokenPipeError, KeyError):
            # Temporary issue; pause and retry
            await asyncio.sleep(5)
