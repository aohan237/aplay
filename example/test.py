import sys
import os
pwd = os.getcwd()
sys.path.append('/'.join(os.getcwd().split('/')[:-1]))
import asyncio
import random
from aplay.kernel.actor import Actor
from aplay.kernel.system import KernelActor
from collections import defaultdict
from copy import deepcopy

class Monitor(Actor):
    def __init__(self, *args, **kwargs):
        super(Monitor, self).__init__(*args, **kwargs)
        self.count_num = defaultdict(int)

    async def prepare_children(self):
        self.displayer = self.create_actor(
            name='display', actor_cls=Displayer)
        self.displayer.start()

    async def msg_handler(self, msg=None):
        if msg is not None:
            msg_type = msg.get('msg_type')
            self.count_num[msg_type] += 1
        await self.displayer.send(deepcopy(self.count_num))


class Displayer(Actor):

    async def msg_handler(self, msg=None):
        if msg is not None:
            print('-----monitor num----', msg)


class Worker(Actor):

    async def prepare_children(self):
        self.worker_monitor = self.create_actor(
            name='count', actor_cls=Monitor)
        self.worker_monitor.start()

    def user_task_callback(self, *args, **kwargs):
        print('--user_task_callback----', args[0].exception(), kwargs)


    async def msg_handler(self, msg=None):
        if msg is None:
            return
        else:
            msg_type = msg.get('msg_type')
            if msg_type == 'text':
                print('--worker--', msg)
            else:
                cc = 1/0
            await self.worker_monitor.send(msg)


class MyKernel(KernelActor):
    def __init__(self, *args, **kwargs):
        super(MyKernel, self).__init__(*args, **kwargs)
        self.actor = self.create_actor(
            name="test", actor_cls=Worker)

    async def msg_handler(self, msg=None):
        print('mykernel', msg)

        for i in range(100):
            tt = random.choice(['text', 'voice'])
            msg = {'msg_type': tt, 'content': f"hello{i}"}
            await self.actor.send(message=msg)


bb = MyKernel("kernel")
bb.send_nowait('start')
bb.start()
