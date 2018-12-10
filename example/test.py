import asyncio
from actor import Actor
from system import KernelActor


class NameActor(Actor):
    async def msg_handler(self, msg=None):
        print("nameactor", msg)


bb = KernelActor("kernel")
n_actor = bb.create_actor(address="user", actor_cls=NameActor)
for i in range(100000):
    n_actor.send(message=f"hello{i}")
old_actor = bb.get_path_actor('/kernel/user')
for i in range(100000):
    n_actor.send(message=f"old_actor{i}")
bb.start()
