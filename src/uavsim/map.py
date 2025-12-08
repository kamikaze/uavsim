#!/usr/bin/env python3
import asyncio
import logging
import sys
from decimal import Decimal

from importlib.resources import files
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlApplicationEngine
from qasync import QEventLoop

from uavsim.bus import bus

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Locator(QObject):
    # Exposed to QML to receive map clicks and emit location updates
    def __init__(self):
        super().__init__()
        self.lat = None
        self.lng = None

    locationUpdate = pyqtSignal(float, float, float, arguments=('lat', 'lng', 'heading',), name='locationUpdate')

    @pyqtSlot(str, str, name='setLocation')
    def set_location(self, lat, lng):
        # Called periodically by QML; we don't pull from a queue anymore
        # Values are updated via telemetry subscriber task that emits locationUpdate
        self.lat = Decimal(lat)
        self.lng = Decimal(lng)

    @pyqtSlot(str, str, name='forceLocation')
    def force_location(self, lat, lng):
        # Publish a forced position to the bus
        try:
            lat_f = float(lat)
            lng_f = float(lng)
        except Exception:
            logger.warning('Invalid lat/lng: %s, %s', lat, lng)
            return

        asyncio.create_task(bus.publish('map.position', (lat_f, lng_f)))


class PIDManager(QObject):
    def __init__(self):
        super().__init__()
        self.kp = None
        self.ki = None
        self.kd = None

    pidUpdate = pyqtSignal(float, float, float, arguments=('kp', 'ki', 'kd',), name='pidUpdate')

    @pyqtSlot(str, str, name='setPID')
    def set_pid(self, kp, ki, kd):
        # Values are updated via telemetry or retained; currently just cache
        try:
            self.kp = float(kp)
            self.ki = float(ki)
            self.kd = float(kd)
        except Exception:
            logger.warning('Invalid PID values: %s, %s, %s', kp, ki, kd)

    @pyqtSlot(float, float, float, name='forcePID')
    def force_pid(self, kp, ki, kd):
        asyncio.create_task(bus.publish('map.pid', (kp, ki, kd)))


async def _telemetry_to_ui(locator: Locator):
    q = bus.subscribe('sim.telemetry')
    while True:
        telemetry = await q.get()
        try:
            lat = float(telemetry['latitude-deg'])
            lng = float(telemetry['longitude-deg'])
            heading = float(telemetry['heading-deg'])
        except Exception as e:
            logger.debug('Bad telemetry: %s', e)
            continue
        # Emit into QML (we are inside the Qt/async loop via qasync)
        locator.locationUpdate.emit(lat, lng, heading)


def run_map(extra_tasks=None):
    app = QGuiApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    engine = QQmlApplicationEngine()
    ctx = engine.rootContext()

    locator = Locator()
    pid_manager = PIDManager()

    ctx.setContextProperty('locator', locator)
    ctx.setContextProperty('pidManager', pid_manager)
    ctx.setContextProperty('main', engine)

    qml_path = files('uavsim.resources') / 'main.qml'
    engine.load(str(qml_path))

    # Start telemetry bridge task before the loop runs; schedule on the loop explicitly
    loop.create_task(_telemetry_to_ui(locator))
    # Schedule extra tasks (other components)
    if extra_tasks:
        for t in extra_tasks:
            try:
                c = t() if callable(t) else t
                loop.create_task(c)
            except Exception as e:
                logger.error('Failed to schedule task: %s', e)

    with loop:
        loop.run_forever()
