from asyncio.queues import Queue
import uuid


class MailBox:
    def __init__(self, *args, **kwargs):
        self._name = kwargs.get('name', str(uuid.uuid1()))
        self._ready = False

    async def ready(self):
        return self._ready

    async def prepare(self):
        raise NotImplementedError

    async def put(self, msg=None):
        raise NotImplementedError

    async def size(self):
        raise NotImplementedError

    async def empty(self):
        raise NotImplementedError

    async def get(self):
        raise NotImplementedError

    async def policy(self):
        """
        used for too many mail, policy, abandon some msg or send warnings
        """
        raise NotImplementedError
