import logging
from aplay.kernel.actor import Actor
from aplay.kernel.system import KernelActor
from sanic import Sanic
from sanic.response import json

msg_logger = logging.getLogger('sanic.access')


class MessageActor(Actor):

    async def msg_handler(self, msg=None):
        print(msg)


app = Sanic()
# app.config.KEEP_ALIVE = False


@app.route('/')
async def test(request):
    actor = request.app.actor
    actor.send({'hello': 'world'})
    return json({'hello': 'world'})


class SanicKernel(KernelActor):

    def __init__(self, *args, **kwargs):
        super(SanicKernel, self).__init__(*args, **kwargs)
        self.app = app
        self.app.actor = self.create_actor('msg', actor_cls=MessageActor)

    async def msg_handler(self, msg=None):
        await self.app.create_server(host="0.0.0.0", port=8000)


bb = SanicKernel("nsq")
bb.send("hahaha")
bb.start()
