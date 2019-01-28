import logging
import websockets
import asyncio
import concurrent
import json
from aplay.kernel.actor import Actor
from aplay.kernel.system import KernelActor
from aplay.mailbox.redis_box import RedisQueue

msg_logger = logging.getLogger('sanic.access')


class SocketActor(Actor):

    def __init__(self, *args, **kwargs):
        super(SocketActor, self).__init__(*args, **kwargs)
        self.websocket = kwargs.get('websocket', None)
        # self.mailbox = RedisQueue(name=self.name)

    def decide_to_start(self):
        if self.websocket is None:
            return False

    def set_websocket(self, websocket):
        self.websocket = websocket

    def reset_websocket(self):
        self.websocket = None

    async def msg_handler(self, msg=None):
        if not isinstance(msg, str):
            msg = json.dumps(msg)
        if self.websocket and msg:
            await self.websocket.send(msg)


class WebsocketKernel(KernelActor):

    def __init__(self, *args, **kwargs):
        super(WebsocketKernel, self).__init__(*args, **kwargs)
        self.websocket_server = websockets.serve(self.tt, 'localhost', 9876)
        self.socket_dict = {}

    async def tt(self, websocket, path):
        self.socket_dict[websocket] = None
        from_actor = None
        while True:
            try:
                data = await asyncio.wait_for(websocket.recv(), 2)
            except websockets.exceptions.ConnectionClosed:
                print('websocket is closed')
                break
            except concurrent.futures._base.TimeoutError:
                print('receive data timeout,websocket is closed:', websocket.closed)
                if websocket.closed:
                    break
                data = None
            print(data)
            if data is not None:

                data = json.loads(data)
                from_user = data.get('from')
                to_user = data.get('to')

                # prepare for user socket
                if from_user not in self.child:
                    from_actor = self.create_actor(
                        name=from_user, actor_cls=SocketActor)
                else:
                    from_actor = self.child.get(from_user)
                if from_actor.websocket is not websocket:
                    from_actor.set_websocket(websocket)
                print('from_actor data:', from_actor.name,
                      from_actor.mailbox.size())

                # 记录websocket的用户
                if websocket not in self.socket_dict:
                    self.socket_dict[websocket] = from_actor
                else:
                    self.socket_dict[websocket] = from_actor

                if to_user not in self.child:
                    self.create_actor(
                        name=to_user, actor_cls=SocketActor)

                print(self.socket_dict, self.child)

                # send data to to user socket
                actor = self.child.get(to_user)
                await actor.send(data)
            # start handle actor
            if from_actor is not None:
                from_actor.start()

        print('websocket is closed,pop from self.socket_dict', self.socket_dict)
        # reset websocket and actor websocket
        self.socket_dict.pop(websocket)
        if from_actor is not None:
            from_actor.reset_websocket()
        print('self.socket_dict pop result', self.socket_dict)

    async def msg_handler(self, msg=None):
        print('kernel msg', msg)
        await self.websocket_server


bb = WebsocketKernel("web")
task = bb.loop.create_task(bb.send("hahaha"))
print(task)
bb.start()
