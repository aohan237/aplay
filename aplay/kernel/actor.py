import asyncio
import weakref
from functools import partial
from .logger import actor_logger
from .const import ACTOR_RUNNING, ACTOR_STARTED, ACTOR_STOPPED, ACTOR_INIT, SEP


class Actor:
    def __init__(
        self,
        loop=None,
        name: str = None,
        parent=None,
        max_tasks=None,
        mail_station=None,
        mail_box_type=None,
        address=None,
        **kwargs,
    ):
        self._name = name
        self._child = {}
        self._monitor = []
        self._runing_state = ACTOR_INIT
        self._human_runing_state = ACTOR_STARTED
        self._parent = parent
        self._max_tasks = max_tasks or 50
        self._running_task = 0
        if mail_station is None:
            raise Exception("mail_station must be not None")
        self._mail_station = mail_station
        self._mail_box_type = mail_box_type
        if address is None:
            self._address = (
                (
                    self._parent._address + SEP
                    if self._parent._address != SEP
                    else self._parent._address
                )
                + self._name
                if self._parent
                else SEP
            )
        else:
            self._address = address

        self.register_self_to_mailstation()
        self._loop = loop or asyncio.get_event_loop()

    def register_self_to_mailstation(self):
        self._mail_station.register_address(self._address, self)

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

    async def check_address_available(self, address):
        if self._address == SEP and address != SEP:
            return True
        level_length = len(address.split(SEP))
        self_level_length = len(self._address.split(SEP))
        if self_level_length < level_length:
            if self._address in address:
                return True
        return False

    async def send_to_address(self, address=None, msg: dict = None):
        if not await self.check_address_available(address):
            actor_logger.info(f"address not available: {self._address} -> {address}")
            return False
        await self._mail_station.send_to_address(address, msg)
        actors = await self._mail_station.get_address_actors(address)
        for actor in actors:
            if actor:
                if msg is not None:
                    if actor._runing_state == ACTOR_RUNNING:
                        pass
                    else:
                        if actor.decide_to_start():
                            actor.start()
                else:
                    actor.handle_panic(msg=msg)
        return False

    def handle_panic(self, msg: dict = None):
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

    def create_actor(self, name=None, actor_cls=None, mail_box_type=None):
        if actor_cls is None:
            actor_logger.exception("wrong actor_cls")
            raise Exception("wrong actor_cls")
        actor = actor_cls(
            name=name,
            parent=self,
            loop=self._loop,
            mail_station=self._mail_station,
            mail_box_type=mail_box_type if mail_box_type else self._mail_box_type,
        )
        self._child[actor._name] = actor
        return weakref.proxy(actor)

    def stop(self):
        self._runing_state = ACTOR_STOPPED
        self._human_runing_state = ACTOR_STOPPED

    def human_start(self):
        self._human_runing_state = ACTOR_STARTED

    def start(self):
        if self._runing_state == ACTOR_STOPPED or self._runing_state == ACTOR_INIT:
            self._loop.create_task(self.handler())
        elif self._runing_state == ACTOR_RUNNING:
            pass

    async def prepare_children(self):
        for _, child in self._child.items():
            if (
                child._runing_state == ACTOR_INIT
                or child._runing_state == ACTOR_STOPPED
            ):
                child.start()

    async def create_msg_task(self, msg):
        task = self._loop.create_task(self.msg_handler(msg))
        m_callback = partial(self.handle_task_done, msg=msg)
        task.add_done_callback(m_callback)
        self._running_task += 1

    async def task_done_new_task(self):
        if self._running_task <= 0:
            self._runing_state = ACTOR_STOPPED

    async def handler(self):
        if self._runing_state == ACTOR_INIT:
            await self.prepare_children()
        self._runing_state = ACTOR_RUNNING
        mailbox = await self._mail_station.get_mailbox(self._address)
        if mailbox is None:
            actor_logger.info(
                f"this address {self._address} has no mailbox please register it first"
            )
        else:
            try:
                while not await mailbox.empty():
                    if self._running_task < self._max_tasks:
                        msg = await mailbox.get()
                        await self.create_msg_task(msg)
                    else:
                        actor_logger.info(
                            f"{self._address} running task exceeds max tasks,waiting"
                        )
                        break
            except Exception as tmp:
                actor_logger.exception(tmp)
        self._runing_state = ACTOR_STOPPED
        actor_logger.info(f"{self._address} stopped")

    async def msg_handler(self, msg=None):
        return NotImplemented

    async def tell(self, msg=None):
        return await self.msg_handler(msg=msg)

    def tell_nowait(self, msg=None):
        task = self._loop.create_task(self.tell(msg=msg))
        return task
