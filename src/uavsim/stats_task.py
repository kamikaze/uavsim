import asyncio
import logging
import os

import h5py
import numpy as np

from uavsim.bus import bus

logger = logging.getLogger(__name__)


async def run_stats(output_dir: str = "/tmp"):
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, 'swmr_telemetry.h5')
    f = h5py.File(file_path, 'a', swmr=True, libver='latest')

    try:
        if 'telemetry' in f:
            telemetry = f['telemetry']
        else:
            telemetry = f.create_group('telemetry')
            telemetry.create_dataset(
                'axis0', chunks=(10,), maxshape=(None,), data=np.array([b'index', b'speed', b'altitude'], dtype='|S5')
            )
            telemetry.create_dataset(
                'axis1', chunks=(10,), maxshape=(None,), data=np.array([], dtype='float64')
            )
            telemetry.create_dataset(
                'block0_items', chunks=(10,), maxshape=(None,),
                data=np.array([b'index', b'speed', b'altitude'], dtype='|S5')
            )
            telemetry.create_dataset(
                'block0_values', chunks=(100, 3), maxshape=(None, 3), data=np.array([[.0, .0, .0]], dtype='float64')
            )

        f.swmr_mode = True

        q = bus.subscribe('sim.telemetry')
        while True:
            t = await q.get()
            try:
                telemetry['block0_values'].resize((len(telemetry['block0_values']) + 1, 3))
                telemetry['block0_values'][-1] = np.array([
                    t['dt'], t['airspeed-kt'], t['altitude-ft']
                ])
                f.flush()
            except Exception as e:
                logger.debug('Failed to write telemetry: %s', e)
    finally:
        try:
            f.close()
        except Exception:
            pass
