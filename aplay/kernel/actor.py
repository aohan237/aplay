import asyncio
import weakref
import time
from .logger import actor_logger
from .const import ACTOR_RUNNING, ACTOR_STARTED, ACTOR_STOPPED


class Actor:
    def __init__(self, address: str=None, loop=None,
                 parent=None, **kwargs):
        self.address = '/' + address
        self.mailbox = asyncio.Queue()
        self.child = {}
        self.monitor = []
        self.runing_state = ACTOR_STOPPED
        self.parent = parent
        self.loop = loop or asyncio.get_event_loop()

    def get_path_actor(self, address: str=None):
        if address.endswith('/'):
            address = address[:-1]
        path = ''
        for i in address.strip('/').split('/'):
            path += '/' + i
            if self.child.get(path):
                if path == address:
                    return weakref.proxy(self.child.get(path))
                else:
                    continue
            else:
                break
        return None

    def send(self, message=None):
        if message is not None:
            self.mailbox.put_nowait(message)
            if self.parent:
                self.parent.send_address(self.address)

    def send_address(self, address=None, msg: {}=None):
        actor = self.child.get(address)
        if actor:
            if not msg:
                if actor.runing_state == ACTOR_STARTED:
                    pass
                else:
                    actor.start()
            else:
                actor.handle_panic(msg=msg)

        # 是否需要启动父actor 存疑
        # if self.runing_state == "stopped" and self.parent:
        #     self.parent.send_address(self.address)

    def handle_panic(self, msg: {}=None):
        actor_logger.info(msg)
        self.start()

    def create_actor(self, address=None, actor_cls=None):
        if actor_cls is None:
            actor_logger.exception("wrong actor_cls")
            raise Exception("wrong actor_cls")
        actor = actor_cls(address=address, parent=self, loop=self.loop)
        self.child[actor.address] = actor
        return weakref.proxy(actor)

    def stop(self):
        self.runing_state = ACTOR_STOPPED

    def start(self):
        if self.runing_state == ACTOR_STOPPED:
            self.runing_state = ACTOR_STARTED
            self.loop.create_task(self.handler())
        elif self.runing_state == ACTOR_RUNNING:
            pass

    async def handler(self):
        now = int(time.time() * 1000)
        self.runing_state = ACTOR_RUNNING
        try:
            while not self.mailbox.empty():
                msg = await self.mailbox.get()
                self.loop.create_task(self.msg_handler(msg))
        except Exception as tmp:
            actor_logger.exception(tmp)
            if self.parent:
                self.parent.send_address(
                    self.address, msg={'error': tmp, 'message': msg})
        self.runing_state = ACTOR_STOPPED
        print('running', int(time.time() * 1000) - now)
        actor_logger.info(f"{self.address} stopped")

    async def msg_handler(self, msg=None):
        return NotImplemented
