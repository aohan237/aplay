import asyncio
from .actor import Actor
from .logger import actor_logger


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
        self.runing_state = 'stopped'

    def start(self, address=None):
        if self.runing_state == "stopped":
            self.runing_state = "started"
        try:
            self.loop.create_task(self.handler())
            self.loop.run_forever()
        except KeyboardInterrupt:
            actor_logger.info('keyboard interrupt,system closed')
