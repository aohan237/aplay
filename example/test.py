import asyncio
from aplay.kernel.actor import Actor
from aplay.kernel.system import KernelActor


class NameActor(Actor):
    async def msg_handler(self, msg=None):
        print("nameactor", msg)

class MyKernel(KernelActor):
    def __init__(self,*args,**kwargs):
        super(MyKernel,self).__init__(*args,**kwargs)
        self.actor = self.create_actor(name="user", actor_cls=NameActor)
    async def msg_handler(self,msg=None):
        print('mykernel',msg)

        for i in range(100000):
            await self.actor.send(message=f"hello{i}")

bb = MyKernel("kernel")
loop=asyncio.get_event_loop()
loop.run_until_complete(bb.send('start'))
bb.start()
