from asyncio.queues import Queue
import uuid


class MailBox:
    def __init__(self, *args, **kwargs):
        self.name = kwargs.get('name', str(uuid.uuid1()))

    async def put(self, msg=None):
        raise NotImplementedError

    async def size(self):
        raise NotImplementedError

    async def empty(self):
        raise NotImplementedError

    async def get(self):
        raise NotImplementedError
