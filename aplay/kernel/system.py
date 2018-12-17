import asyncio
from .actor import Actor
from .logger import actor_logger
from .const import ACTOR_RUNNING, ACTOR_STARTED, ACTOR_STOPPED


class KernelActor(Actor):
    def __init__(self, address: str=None, loop=None,
                 parent=None, max_workers=None, **kwargs):
        super(KernelActor, self).__init__(
            address=address, loop=loop,
            parent=parent, **kwargs)
        self.address = address
        self.parent = None
        self.loop = loop or asyncio.get_event_loop()

    def stop(self):
        self.runing_state = ACTOR_STOPPED

    def start(self, address=None):
        if self.runing_state == ACTOR_STOPPED:
            self.runing_state = ACTOR_STARTED
        try:
            self.loop.create_task(self.handler())
            self.loop.run_forever()
        except KeyboardInterrupt:
            actor_logger.info('keyboard interrupt,system closed')
