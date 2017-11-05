#!/usr/bin/env python3
import asyncio
import logging
import sys

from decimal import Decimal
from queue import Queue
from threading import Thread

from PyQt5.QtCore import pyqtSlot, QObject, pyqtSignal
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlApplicationEngine
from autobahn.asyncio.wamp import ApplicationRunner, ApplicationSession
from autobahn.wamp import RegisterOptions

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)

CROSSBAR_ROUTE = 'ws://127.0.0.1:8091/qgpsemu'


class MapComponent(ApplicationSession):
    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)
        self.queue_to_ui = config.extra['queue_to_ui']
        self.is_running = False

    async def on_sim_nmea(self, nmea_sentence):
        self.queue_to_ui.put(('23.00', '33.11', ))
        # llocator.locationUpdate.emit('23.00', '33.11')
        logger.info(nmea_sentence)

    async def onJoin(self, details):
        await self.register(self, options=RegisterOptions(invoke='roundrobin'))

        await self.subscribe(self.on_sim_nmea, 'sim.nmea')

        self.is_running = True

        while self.is_running:
            await asyncio.sleep(25)


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


class Locator(QObject):
    def __init__(self, queue_to_ui):
        super().__init__()

        self.queue_to_ui = queue_to_ui
        self.lat = None
        self.lng = None

    locationUpdate = pyqtSignal(str, str, arguments=['lat', 'lng'], name='locationUpdate')

    # Slot for summing two numbers
    @pyqtSlot(str, str, name='setLocation')
    def set_location(self, lat, lng):
        self.lat = Decimal(lat)
        self.lng = Decimal(lng)
        logger.debug('Set location: {}, {}'.format(lat, lng))


def run_map_ui(queue_to_ui):
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    ctx = engine.rootContext()

    locator = Locator(queue_to_ui)

    ctx.setContextProperty('locator', locator)
    ctx.setContextProperty('main', engine)
    engine.load('main.qml')

    sys.exit(app.exec_())


if __name__ == '__main__':
    queue_to_ui = Queue()

    thread = Thread(target=run_map_ui, args=(queue_to_ui, ))
    thread.start()

    join_to_router(MapComponent, {'queue_to_ui': queue_to_ui})

    thread.join()
