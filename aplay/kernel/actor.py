import asyncio
import weakref
import time
from .logger import actor_logger
from .const import ACTOR_RUNNING, ACTOR_STARTED, ACTOR_STOPPED


class Actor:
    def __init__(self, loop=None, name: str=None,
                 parent=None, **kwargs):
        self.name = name
        self.mailbox = asyncio.Queue()
        self.child = {}
        self.monitor = []
        self.runing_state = ACTOR_STOPPED
        self.parent = parent
        if self.parent:
            self.address = self.parent.address + '/' + self.name
        else:
            self.address = '/'
        self.loop = loop or asyncio.get_event_loop()

    def get_path_actor(self, address: str=None):
        if address.endswith('/'):
            address = address[:-1]
        path = ''
        child_actor = self.child
        for i in address.strip('/').split('/'):
            path += '/' + i
            if child_actor.get(i):
                if path == address:
                    return weakref.proxy(child_actor.get(i))
                else:
                    child_actor = child_actor.get(i)
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

    def handle_task_done(self, *args, **kwargs):
        pass

    def create_actor(self, name=None, actor_cls=None):
        if actor_cls is None:
            actor_logger.exception("wrong actor_cls")
            raise Exception("wrong actor_cls")
        actor = actor_cls(name=name, parent=self, loop=self.loop)
        self.child[actor.name] = actor
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
        self.runing_state = ACTOR_RUNNING
        try:
            while not self.mailbox.empty():
                msg = await self.mailbox.get()
                task = self.loop.create_task(self.msg_handler(msg))
                task.add_done_callback(self.handle_task_done)
        except Exception as tmp:
            actor_logger.exception(tmp)
            if self.parent:
                self.parent.send_address(
                    self.address, msg={'error': tmp, 'message': msg})
        self.runing_state = ACTOR_STOPPED
        actor_logger.info(f"{self.address} stopped")

    async def msg_handler(self, msg=None):
        return NotImplemented

    async def tell(self, msg=None):
        return await self.msg_handler(msg=msg)
