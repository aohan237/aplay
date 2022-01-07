import pickle
import uuid
from .base import MailBox


class RedisQueueMailBox(MailBox):
    """A subclass of Queue that retrieves most recently added entries first."""

    def __init__(self, pool=None, name=None):
        self._name = name if name is not None else str(uuid.uuid1())
        self._pool = pool

    async def prepare(self):
        pass

    async def put(self, msg=None):
        await self._pool.lpush(self._name, self.dumps_msg(msg))

    async def size(self):
        return await self._pool.llen(self._name)

    async def empty(self):
        length = await self.size()
        return length == 0

    async def get(self):
        raw_data = await self._pool.rpop(self._name)
        return self.loads_msg(raw_data)

    def dumps_msg(self, msg=None):
        if msg is None:
            return ""
        return pickle.dumps(msg)

    def loads_msg(self, msg=None):
        if msg is None:
            return None
        return pickle.loads(msg)
