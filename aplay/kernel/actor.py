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
        self._name = name
        mailbox = mailbox or QueueMailBox
        self._mailbox = mailbox(name=name, mail_address=mail_address)
        self._child = {}
        self._monitor = []
        self._runing_state = ACTOR_INIT
        self._human_runing_state = ACTOR_STARTED
        self._parent = parent
        self._max_tasks = max_tasks or 50
        self._running_task = 0
        self._kernel = kernel
        if self._parent:
            if self._parent._address == '/':
                self._address = self._parent._address + self._name
            else:
                self._address = self._parent._address + '/' + self._name
        else:
            self._address = '/'
        self._loop = loop or asyncio.get_event_loop()

    def get_actor(self, name=None):
        actor = self._child.get(name)
        if actor:
            return weakref.proxy(actor)
        else:
            return None

    def decide_to_start(self):
        """
        decide to start or not
        """
        if self._human_runing_state == ACTOR_STOPPED:
            return False
        else:
            return True

    def get_abs_path_actor(self, address: str = None):
        """
        get the corresponding actor ,only use address
        """
        root_path = '/'
        if address.endswith(root_path) and address != '/':
            address = address[:-1]
        path = self._kernel.address
        compare_address = address.replace(self._address + root_path, '')
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
                    child_actor = tmp_child_actor._child
                    continue
            else:
                break
        return None

    def get_path_actor(self, address: str = None):
        root_path = '/'
        if address.endswith(root_path):
            address = address[:-1]
        path = self._address
        compare_address = address.replace(self._address + root_path, '')
        child_actor = self._child
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
                    child_actor = tmp_child_actor._child
                    continue
            else:
                break
        return None

    async def send(self, message=None):
        if message is not None:
            if self._parent:
                self._parent.send_address(self._address)
            await self.prepare_mailbox()
            await self._mailbox.put(message)

    def send_nowait(self, message=None):
        task = self._loop.create_task(self.send(message=message))
        return task

    def send_address(self, address=None, msg: {} = None):
        actor = self.get_path_actor(address)
        if actor:
            if not msg:
                if actor._runing_state == ACTOR_RUNNING:
                    pass
                else:
                    if actor.decide_to_start():
                        actor.start()
            else:
                actor.handle_panic(msg=msg)

        # 是否需要启动父actor 存疑
        # if self._runing_state == "stopped" and self._parent:
        #     self._parent.send_address(self._address)

    def handle_panic(self, msg: {} = None):
        actor_logger.info(msg)
        self.start()

    def handle_task_done(self, *args, **kwargs):
        self._running_task -= 1
        self._loop.create_task(self.task_done_new_task())
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
                          loop=self._loop, kernel=self._kernel)
        self._child[actor._name] = actor
        return weakref.proxy(actor)

    def stop(self):
        self._runing_state = ACTOR_STOPPED
        self._human_runing_state = ACTOR_STOPPED

    def human_start(self):
        self._human_runing_state = ACTOR_STARTED

    def start(self):
        if self._runing_state == ACTOR_STOPPED or \
                self._runing_state == ACTOR_INIT:
            self._loop.create_task(self.handler())
        elif self._runing_state == ACTOR_RUNNING:
            pass

    async def prepare_children(self):
        pass

    async def prepare_mailbox(self):
        if not self._mailbox.ready:
            await self._mailbox.prepare()

    async def create_msg_task(self):
        msg = await self._mailbox.get()
        task = self._loop.create_task(self.msg_handler(msg))
        m_callback = partial(self.handle_task_done, msg=msg)
        task.add_done_callback(m_callback)
        self._running_task += 1

    async def task_done_new_task(self):
        if not await self._mailbox.empty():
            await self.create_msg_task()
        if self._running_task <= 0:
            self._runing_state = ACTOR_STOPPED

    async def handler(self):
        if self._runing_state == ACTOR_INIT:
            await self.prepare_children()
            await self.prepare_mailbox()
        self._runing_state = ACTOR_RUNNING
        try:
            while not await self._mailbox.empty():
                if self._running_task < self._max_tasks:
                    await self.create_msg_task()
                else:
                    actor_logger.info(
                        f'{self._address} running task exceeds max tasks,waiting')
                    break
        except Exception as tmp:
            actor_logger.exception(tmp)
        self._runing_state = ACTOR_STOPPED
        actor_logger.info(f"{self._address} stopped")

    async def msg_handler(self, msg=None):
        return NotImplemented

    async def tell(self, msg=None):
        return await self.msg_handler(msg=msg)
