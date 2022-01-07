import sys
import os

pwd = os.getcwd()
sys.path.append("/".join(os.getcwd().split("/")[:-1]))
import asyncio
import random
from aplay.kernel.actor import Actor
from aplay.kernel.system import KernelActor
from aplay.mailstation.hash_redis import HashRedisMailStation

from collections import defaultdict
from copy import deepcopy


class Monitor(Actor):
    def __init__(self, *args, **kwargs):
        super(Monitor, self).__init__(*args, **kwargs)
        self.count_num = defaultdict(int)
        self.displayer = self.create_actor(name="display", actor_cls=Displayer)

    async def msg_handler(self, msg=None):
        if msg is not None:
            msg_type = msg.get("msg_type")
            self.count_num[msg_type] += 1
        await self.displayer.tell(deepcopy(self.count_num))


class Displayer(Actor):
    async def msg_handler(self, msg=None):
        if msg is not None:
            print("-----monitor num----", msg)
        await self.send_to_address("/test", msg)


class Worker(Actor):
    def __init__(self, *args, **kwargs):
        super(Worker, self).__init__(*args, **kwargs)
        self.worker_monitor = self.create_actor(name="count", actor_cls=Monitor)

    def user_task_callback(self, *args, **kwargs):
        print("--user_task_callback----", args[0].exception(), kwargs)

    async def msg_handler(self, msg=None):
        print("worker--", msg)
        if msg is None:
            return
        else:
            msg_type = msg.get("msg_type")
            if msg_type == "text":
                print("--text--", msg)
            else:
                # cc = 1 / 0
                print("--voice--", msg)
            await self.worker_monitor.tell(msg)


class MyKernel(KernelActor):
    def __init__(self, name=None, mail_station=None, **kwargs):
        print(mail_station, kwargs)
        super(MyKernel, self).__init__(name=name, mail_station=mail_station, **kwargs)
        self.actor = self.create_actor(name="test", actor_cls=Worker)

    async def msg_handler(self, msg=None):
        print("mykernel", msg)

        for i in range(100):
            tt = random.choice(["voice", "text"])
            msg = {"msg_type": tt, "content": f"hello voice{i}"}
            await self.send_to_address("/test", msg)
        print(self._mail_station._address_book)


bb = MyKernel(
    "kernel", mail_station=HashRedisMailStation(station_address="redis://10.64.146.231")
)
bb.tell_nowait("start")
bb.start()
