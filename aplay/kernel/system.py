import asyncio
import weakref
from .actor import Actor
from .logger import actor_logger
from .const import ACTOR_STARTED, ACTOR_STOPPED


class KernelActor(Actor):
    def __init__(self, name: str = None, loop=None,
                 parent=None, max_workers=None, **kwargs):
        super(KernelActor, self).__init__(
            name=name, loop=loop,
            parent=parent, **kwargs)
        self._kernel = weakref.proxy(self)

    def stop(self):
        self._runing_state = ACTOR_STOPPED
        self._human_runing_state = ACTOR_STOPPED
        self._loop.stop()
        actor_logger.info('system loop stopped,exit')

    def kernel_run(self):
        self._loop.create_task(self.handler())
        self._loop.run_forever()

    def start(self, address=None):

        if self._runing_state == ACTOR_STOPPED:
            self._runing_state = ACTOR_STARTED
        try:
            self.kernel_run()
        except KeyboardInterrupt:
            actor_logger.info('keyboard interrupt,system closed')
        finally:
            actor_logger.info('system loop stopped,exit')
