#!/usr/bin/env python3
import asyncio
import logging

from autobahn import wamp
from autobahn.wamp.types import RegisterOptions
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner

logger = logging.getLogger(__name__)

CROSSBAR_ROUTE = 'ws://127.0.0.1:8091/qgpsemu'


class SimAdapterComponent(ApplicationSession):
    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)

    # @wamp.subscribe('uav.cmd')
    # async def on_uav_cmd(self, cmd_id, data):
    #     logger.debug(cmd_id, data)

    async def onJoin(self, details):
        await self.register(self, options=RegisterOptions(invoke='roundrobin'))

        async def on_uav_cmd(cmd_id, data):
            logger.debug(cmd_id, data)

        await self.subscribe(on_uav_cmd, 'uav.cmd')


def join_to_router(component_class):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    runner = ApplicationRunner(
        CROSSBAR_ROUTE,
        'qgpsemu'
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
    join_to_router(SimAdapterComponent)

