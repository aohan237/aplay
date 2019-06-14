import asyncio
import weakref
from functools import partial
from .logger import actor_logger
from .const import ACTOR_RUNNING, ACTOR_STARTED, ACTOR_STOPPED, ACTOR_INIT
from aplay.mailbox.queue_mailbox import QueueMailBox


class Actor:
    def __init__(self, loop=None, name: str = None, mailbox=None,
                 parent=None, max_tasks=None, mail_address=None,
                 kernel=None,
                 **kwargs):
        self.name = name
        mailbox = mailbox or QueueMailBox
        self.mailbox = mailbox(name=name, mail_address=mail_address)
        self.child = {}
        self.monitor = []
        self.runing_state = ACTOR_INIT
        self.human_runing_state = ACTOR_STARTED
        self.parent = parent
        self.max_tasks = max_tasks or 50
        self.running_task = 0
        self._kernel = kernel
        if self.parent:
            if self.parent.address == '/':
                self.address = self.parent.address + self.name
            else:
                self.address = self.parent.address + '/' + self.name
        else:
            self.address = '/'
        self.loop = loop or asyncio.get_event_loop()

    def get_actor(self, name=None):
        actor = self.child.get(name)
        if actor:
            return weakref.proxy(actor)
        else:
            return None

    def decide_to_start(self):
        if self.human_runing_state == ACTOR_STOPPED:
            return False
        else:
            return True

    def get_abs_path_actor(self, address: str = None):
        root_path = '/'
        if address.endswith(root_path) and address != '/':
            address = address[:-1]
        path = self._kernel.address
        compare_address = address.replace(self.address + root_path, '')
        child_actor = self._kernel.child
        for i in compare_address.strip(root_path).split(root_path):
            if path == root_path:
                path += i
            else:
                path += root_path + i
            tmp_child_actor = child_actor.get(i)
            if tmp_child_actor:
                if path == address:
                    return weakref.proxy(tmp_child_actor)
                else:
                    child_actor = tmp_child_actor.child
                    continue
            else:
                break
        return None

    def get_path_actor(self, address: str = None):
        root_path = '/'
        if address.endswith(root_path):
            address = address[:-1]
        path = self.address
        compare_address = address.replace(self.address + root_path, '')
        child_actor = self.child
        for i in compare_address.strip(root_path).split(root_path):
            if path == root_path:
                path += i
            else:
                path += root_path + i
            tmp_child_actor = child_actor.get(i)
            if tmp_child_actor:
                if path == address:
                    return weakref.proxy(tmp_child_actor)
                else:
                    child_actor = tmp_child_actor.child
                    continue
            else:
                break
        return None

    async def send(self, message=None):
        if message is not None:
            await self.mailbox.put(message)
            if self.parent:
                self.parent.send_address(self.address)

    def send_nowait(self, message=None):
        task = self.loop.create_task(self.send(message=message))
        return task

    def send_address(self, address=None, msg: {} = None):
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

    def handle_panic(self, msg: {} = None):
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
        actor = actor_cls(name=name, parent=self,
                          loop=self.loop, kernel=self._kernel)
        self.child[actor.name] = actor
        return weakref.proxy(actor)

    def stop(self):
        self.runing_state = ACTOR_STOPPED
        self.human_runing_state = ACTOR_STOPPED

    def human_start(self):
        self.human_runing_state = ACTOR_STARTED

    def start(self):
        if self.runing_state == ACTOR_STOPPED or \
                self.runing_state == ACTOR_INIT:
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
        if self.runing_state == ACTOR_INIT:
            await self.mailbox.prepare()
        self.runing_state = ACTOR_RUNNING
        try:
            while not await self.mailbox.empty():
                if self.running_task < self.max_tasks:
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
