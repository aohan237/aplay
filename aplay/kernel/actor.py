import asyncio
import weakref
import time
from functools import partial
from .logger import actor_logger
from .const import ACTOR_RUNNING, ACTOR_STARTED, ACTOR_STOPPED
from aplay.mailbox.queue_mailbox import QueueMailBox


class Actor:
    def __init__(self, loop=None, name: str=None,
                 parent=None, max_tasks=None, **kwargs):
        self.name = name
        self.mailbox = QueueMailBox(name=name)
        self.child = {}
        self.monitor = []
        self.runing_state = ACTOR_STOPPED
        self.human_runing_state = ACTOR_STARTED
        self.parent = parent
        self.max_tasks = max_tasks or 50
        self.running_task = 0
        if self.parent:
            if self.parent.address == '/':
                self.address = self.parent.address + self.name
            else:
                self.address = self.parent.address + '/' + self.name
        else:
            self.address = '/'
        self.loop = loop or asyncio.get_event_loop()

    def decide_to_start(self):
        if self.human_runing_state == ACTOR_STOPPED:
            return False
        else:
            return True

    def get_path_actor(self, address: str=None):
        if address.endswith('/'):
            address = address[:-1]
        path = self.address
        compare_address = address.strip(self.address)
        child_actor = self.child
        for i in compare_address.strip('/').split('/'):
            if path == '/':
                path += i
            else:
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

    async def send(self, message=None):
        if message is not None:
            await self.mailbox.put(message)
            if self.parent:
                self.parent.send_address(self.address)

    def send_address(self, address=None, msg: {}=None):

        actor = self.get_path_actor(address)
        if actor:
            if not msg:
                if actor.runing_state == ACTOR_RUNNING:
                    pass
                else:
                    if self.decide_to_start():
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
        self.running_task -= 1
        self.loop.create_task(self.task_done_new_task())
        try:
            self.user_task_callback(*args, **kwargs)
        except Exception as tmp:
            actor_logger.exception(tmp)

    def user_task_callback(self, *args, **kwargs):
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
        self.human_runing_state = ACTOR_STOPPED

    def human_start(self):
        self.human_runing_state = ACTOR_STARTED

    def start(self):
        if self.runing_state == ACTOR_STOPPED:
            self.runing_state = ACTOR_STARTED
            self.loop.create_task(self.handler())
        elif self.runing_state == ACTOR_RUNNING:
            pass

    async def create_msg_task(self):
        msg = await self.mailbox.get()
        task = self.loop.create_task(self.msg_handler(msg))
        m_callback = partial(self.handle_task_done, msg=msg)
        task.add_done_callback(m_callback)
        self.running_task += 1

    async def task_done_new_task(self):
        if not await self.mailbox.empty():
            await self.create_msg_task()
        if self.running_task <= 0:
            self.runing_state = ACTOR_STOPPED

    async def handler(self):
        self.runing_state = ACTOR_RUNNING
        try:
            while not await self.mailbox.empty():
                if self.running_task <= self.max_tasks:
                    await self.create_msg_task()
                else:
                    actor_logger.info(
                        f'{self.address} running task exceeds max tasks,waiting')
                    break
        except Exception as tmp:
            actor_logger.exception(tmp)
        self.runing_state = ACTOR_STOPPED
        actor_logger.info(f"{self.address} stopped")

    async def msg_handler(self, msg=None):
        return NotImplemented

    async def tell(self, msg=None):
        return await self.msg_handler(msg=msg)
