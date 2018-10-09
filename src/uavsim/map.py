#!/usr/bin/env python3
import asyncio
import logging
import sys

from decimal import Decimal
from collections import deque
from threading import Thread

from PyQt5.QtCore import pyqtSlot, QObject, pyqtSignal
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlApplicationEngine
from autobahn.asyncio.wamp import ApplicationRunner, ApplicationSession
from autobahn.wamp import RegisterOptions
from pkg_resources import resource_filename

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)

CROSSBAR_ROUTE = 'ws://127.0.0.1:8091/uavsim'


class MapComponent(ApplicationSession):
    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)
        self.queue_to_ui = config.extra['queue_to_ui']
        self.queue_to_sim = config.extra['queue_to_sim']
        self.is_running = False

    async def on_sim_telemetry(self, telemetry):
        try:
            lat = telemetry['latitude-deg']
            lng = telemetry['longitude-deg']
            heading = telemetry['heading-deg']

            self.queue_to_ui.append((lat, lng, heading))
        except KeyError as e:
            logger.error(e)

    async def on_ui_position_force(self):
        try:
            lat, lon = self.queue_to_sim.pop()

            self.publish('map.position', lat, lon)
        except IndexError:
            pass

    async def onJoin(self, details):
        await self.register(self, options=RegisterOptions(invoke='roundrobin'))

        await self.subscribe(self.on_sim_telemetry, 'sim.telemetry')

        self.is_running = True

        while self.is_running:
            await self.on_ui_position_force()
            await asyncio.sleep(0.1)


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


class Locator(QObject):
    # https://stackoverflow.com/questions/50609986/how-to-connect-python-and-qml-with-pyside2
    def __init__(self, queue_to_ui, queue_to_sim):
        super().__init__()

        self.queue_to_ui = queue_to_ui
        self.queue_to_sim = queue_to_sim
        self.lat = None
        self.lng = None

    locationUpdate = pyqtSignal(float, float, float, arguments=('lat', 'lng', 'heading',), name='locationUpdate')

    @pyqtSlot(str, str, name='setLocation')
    def set_location(self, lat, lng):
        self.lat = Decimal(lat)
        self.lng = Decimal(lng)

        try:
            pos = self.queue_to_ui.pop()
            # logger.info('onLocationUpdate: {}'.format(pos))

            self.locationUpdate.emit(*pos)
        except IndexError:
            pass

    @pyqtSlot(str, str, name='forceLocation')
    def force_location(self, lat, lng):
        # self.lat = Decimal(lat)
        # self.lng = Decimal(lng)

        try:
            self.queue_to_sim.append((lat, lng,))
        except IndexError:
            pass


def run_map_ui(queue_to_ui, queue_to_sim):
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    ctx = engine.rootContext()

    locator = Locator(queue_to_ui, queue_to_sim)

    ctx.setContextProperty('locator', locator)
    ctx.setContextProperty('main', engine)
    engine.load(resource_filename('uavsim.resources', 'main.qml'))

    sys.exit(app.exec_())


def main():
    queue_to_ui = deque(maxlen=1)
    queue_to_sim = deque(maxlen=1)

    thread = Thread(target=run_map_ui, args=(queue_to_ui, queue_to_sim,))
    thread.start()

    join_to_router(MapComponent, {'queue_to_ui': queue_to_ui, 'queue_to_sim': queue_to_sim})

    thread.join()


if __name__ == '__main__':
    main()
