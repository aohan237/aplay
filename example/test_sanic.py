# works for sanic==20.12.4, sanic is rapidly breaking changes, so we need to test sanic==20.12.3
import sys
import os

pwd = os.getcwd()
sys.path.append("/".join(os.getcwd().split("/")[:-1]))
import logging
from aplay.kernel.actor import Actor
from aplay.kernel.system import KernelActor
from aplay.mailstation.simple import HashMailStation

from sanic import Sanic
from sanic.response import json
import json as ujson
import asyncio
import time
import uvloop

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

msg_logger = logging.getLogger("sanic.access")


class MessageActor(Actor):
    def __init__(self, *args, **kwargs):
        super(MessageActor, self).__init__(*args, **kwargs)
        self._max_tasks = 10

    async def msg_handler(self, msg=None):
        print("msg_handler", msg)
        await asyncio.sleep(1)


app = Sanic(name="aplay", log_config=None)
# app.config.KEEP_ALIVE = False


app = Sanic("MyHelloWorldApp")


@app.get("/")
async def test(request):
    actor = request.app.actor
    await actor.tell(msg={"hello": "sss"})
    return json({"hello": "sss"})


class SanicKernel(KernelActor):
    def __init__(self, *args, **kwargs):
        super(SanicKernel, self).__init__(*args, **kwargs)
        self.app = app
        self.app.actor = self.create_actor("msg", actor_cls=MessageActor)

    async def msg_handler(self, msg=None):
        """
        sanic loop does not support use loop outside,only this way can do
        """

        await self.app.create_server(
            host="0.0.0.0", port=8000, return_asyncio_server=True
        )


bb = SanicKernel("sanic", mail_station=HashMailStation())
bb.tell_nowait("start")
bb.start()
