import asyncio
from .actor import Actor
from .logger import actor_logger
from .const import ACTOR_STARTED, ACTOR_STOPPED


class KernelActor(Actor):
    def __init__(self, name: str=None, loop=None,
                 parent=None, max_workers=None, **kwargs):
        super(KernelActor, self).__init__(
            name=name, loop=loop,
            parent=parent, **kwargs)

    def stop(self):
        self.runing_state = ACTOR_STOPPED
        self.human_runing_state = ACTOR_STOPPED
        self.loop.stop()
        actor_logger.info('system loop stopped,exit')

    def start(self, address=None):

        if self.runing_state == ACTOR_STOPPED:
            self.runing_state = ACTOR_STARTED
        try:
            self.loop.create_task(self.handler())
            self.loop.run_forever()
        except KeyboardInterrupt:
            actor_logger.info('keyboard interrupt,system closed')
        finally:
            actor_logger.info('system loop stopped,exit')
