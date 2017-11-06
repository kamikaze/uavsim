#!/usr/bin/env python3
import argparse
import asyncio
import logging
import os.path
import sys

import h5py
import numpy as np
from autobahn import wamp
from autobahn.wamp.types import RegisterOptions
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner


logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

CROSSBAR_ROUTE = 'ws://127.0.0.1:8091/uavsim'


class StatisticsComponent(ApplicationSession):
    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)
        self.is_running: bool = False
        file_path = os.path.join(config.extra['output_dir'], 'swmr_telemetry.h5')
        self._output_file = h5py.File(file_path, 'a', swmr=True, libver='latest')

        if 'telemetry' in self._output_file:
            self.telemetry = self._output_file['telemetry']
        else:
            self.telemetry = self._output_file.create_group('telemetry')
            self.telemetry.create_dataset(
                'axis0', chunks=(10,), maxshape=(None,), data=np.array([b'index', b'speed', b'altitude'], dtype='|S5')
            )
            self.telemetry.create_dataset(
                'axis1', chunks=(10,), maxshape=(None,), data=np.array([], dtype='float64')
            )
            self.telemetry.create_dataset(
                'block0_items', chunks=(10,), maxshape=(None,),
                data=np.array([b'index', b'speed', b'altitude'], dtype='|S5')
            )
            self.telemetry.create_dataset(
                'block0_values', chunks=(100, 3), maxshape=(None, 3), data=np.array([[.0, .0, .0]], dtype='float64')
            )

        self._output_file.swmr_mode = True

    # @wamp.subscribe('sim.telemetry')
    async def on_sim_telemetry(self, telemetry):
        self.telemetry['block0_values'].resize((len(self.telemetry['block0_values'])+1, 3))
        self.telemetry['block0_values'][-1] = np.array([
            telemetry['dt'], telemetry['airspeed-kt'], telemetry['altitude-ft']
        ])
        self._output_file.flush()

    async def onJoin(self, details):
        await self.register(self, options=RegisterOptions(invoke='roundrobin'))

        await self.subscribe(self.on_sim_telemetry, 'sim.telemetry')

        self.is_running = True

        while self.is_running:
            await asyncio.sleep(0.1)

    async def onLeave(self, details):
        logger.debug('Closing output file')
        self.output_file.close()


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
        description='Statistics writer',
    )
    parser.add_argument(
        '--output-dir',
        dest='output_dir',
        help='Output directory for statistics',
        default='/tmp'
    )

    args = parser.parse_args(sys.argv[1:])

    join_to_router(StatisticsComponent, {'output_dir': args.output_dir})
