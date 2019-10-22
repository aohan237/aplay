import aioredis
import pickle
from .base import MailBox


class RedisQueue(MailBox):
    """A subclass of Queue that retrieves most recently added entries first."""

    def __init__(self, *args, mail_address=None, **kwargs):
        super(RedisQueue, self).__init__(*args, **kwargs)
        self._redis_uri = mail_address or 'redis://127.0.0.1'
        self._pool = None

    async def connect_pool(self):
        if self._pool is None:
            self._pool = await aioredis.create_redis_pool(
                self._redis_uri)
            self._ready = True

    async def prepare(self):
        await self.connect_pool()

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
            return ''
        return pickle.dumps(msg)

    def loads_msg(self, msg=None):
        if msg is None:
            return None
        return pickle.loads(msg)
