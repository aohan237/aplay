import os
import sys

pwd = os.getcwd()
sys.path.append("/".join(os.getcwd().split("/")[:-1]))
import asyncio
import random
from collections import defaultdict
from copy import deepcopy

from aplay.kernel.actor import Actor
from aplay.kernel.system import KernelActor
from aplay.mailstation.simple import HashMailStation
from aplay.msg.msg import Msg, format_msg


class Worker(Actor):
    def __init__(self, *args, **kwargs):
        super(Worker, self).__init__(*args, **kwargs)

    def user_task_callback(self, *args, **kwargs):
        excep = args[0].exception()
        if excep is not None:
            print("--user_error--", excep, kwargs)
        else:
            print("--finish--", kwargs)

    async def msg_handler(self, msg=None):
        print("worker--", msg)
        body = msg.get("body")
        if msg is None:
            return
        else:
            msg_type = body.get("msg_type")
            if msg_type == "text":
                msg = format_msg(
                    self._address,
                    flow_id=msg.flow_id,
                    flow_index=msg.flow_index,
                    body=body,
                )
                print("--text--", msg)
            else:
                print("--voice--", msg)


class MyKernel(KernelActor):
    def __init__(self, name=None, mail_station=None, **kwargs):
        print(mail_station, kwargs)
        super(MyKernel, self).__init__(name=name, mail_station=mail_station, **kwargs)
        self.actor = self.create_actor(name="test", actor_cls=Worker)

    async def msg_handler(self, msg=None):
        print("mykernel", msg)

        for i in range(100):
            tt = random.choice(["voice", "text"])
            body = {"msg_type": tt, "content": f"hello voice{i}"}
            msg = format_msg(self._address, body=body)
            print(msg)
            await self.send_to_address("/test", msg)


bb = MyKernel("kernel", mail_station=HashMailStation())
bb.tell_nowait("start")
bb.start()
