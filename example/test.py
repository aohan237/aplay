import asyncio
from aplay.kernel.actor import Actor
from aplay.kernel.system import KernelActor


class NameActor(Actor):
    async def msg_handler(self, msg=None):
        print("nameactor", msg)
        tmp_actor = self.get_abs_path_actor('/test')
        print(tmp_actor)


class TestActor(Actor):
    def __init__(self, *args, **kwargs):
        super(TestActor, self).__init__(*args, **kwargs)
        self.actor = self.create_actor(
            name="name", actor_cls=NameActor)

    async def msg_handler(self, msg=None):
        print(self._kernel.child)
        if msg == 'tt':
            print('tt', msg)
            self._kernel.stop()
        else:
            print('test actor', msg)
            await self.actor.send(message=msg)


class MyKernel(KernelActor):
    def __init__(self, *args, **kwargs):
        super(MyKernel, self).__init__(*args, **kwargs)
        self.actor = self.create_actor(
            name="test", actor_cls=TestActor)

    async def msg_handler(self, msg=None):
        print('mykernel', msg)

        for i in range(100):
            await self.actor.send(message=f"hello{i}")


bb = MyKernel("kernel")
bb.send_nowait('start')
bb.start()
