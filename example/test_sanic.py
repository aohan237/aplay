import logging
from aplay.kernel.actor import Actor
from aplay.kernel.system import KernelActor
from sanic import Sanic
from sanic.response import json
import json as ujson
import asyncio
import time

msg_logger = logging.getLogger('sanic.access')


class MessageActor(Actor):
    def __init__(self, *args, **kwargs):
        super(MessageActor, self).__init__(*args, **kwargs)
        self.max_tasks = 10

    async def msg_handler(self, msg=None):
        print('msg_handler', msg)
        await asyncio.sleep(5)


app = Sanic(log_config=None)
# app.config.KEEP_ALIVE = False


@app.route('/')
async def test(request):
    actor = request.app.actor
    await actor.send(message={'hello': 'world'})
    return json({'hello': 'world'})


class SanicKernel(KernelActor):

    def __init__(self, *args, **kwargs):
        super(SanicKernel, self).__init__(*args, **kwargs)
        self.app = app
        self.app.actor = self.create_actor('msg', actor_cls=MessageActor)

    async def msg_handler(self, msg=None):
        await self.app.create_server(host="0.0.0.0", port=8000)


bb = SanicKernel("nsq")
loop = asyncio.get_event_loop()
loop.create_task(bb.send("hahaha"))
bb.start()
