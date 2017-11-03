#!/usr/bin/env python3
import logging
import sys

from decimal import Decimal

from PyQt5.QtCore import pyqtSlot, QObject, pyqtSignal
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlApplicationEngine


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Locator(QObject):
    location_update = pyqtSignal(str, str, arguments=['lat', 'lng'])

    # Slot for summing two numbers
    @pyqtSlot(str, str)
    def set_location(self, lat, lng):
        lat = Decimal(lat)
        lng = Decimal(lng)
        logger.debug('Set location: {}, {}'.format(lat, lng))


if __name__ == '__main__':
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    locator = Locator()
    ctx = engine.rootContext()

    ctx.setContextProperty('locator', locator)
    ctx.setContextProperty('main', engine)
    engine.load('main.qml')

    sys.exit(app.exec_())
