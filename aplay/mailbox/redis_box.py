import aioredis
import json
import pickle
from .base import MailBox


class RedisQueue(MailBox):
    """A subclass of Queue that retrieves most recently added entries first."""

    def __init__(self, *args, **kwargs):
        super(RedisQueue, self).__init__(*args, **kwargs)
        self.redis_uri = kwargs.get('redis_uri', 'redis://127.0.0.1')
        self.pool = None

    async def connect_pool(self):
        if self.pool is None:
            self.pool = await aioredis.create_redis_pool(
                self.redis_uri)

    async def put(self, msg=None):
        await self.connect_pool()
        await self.pool.lpush(self.name, self.dumps_msg(msg))

    async def size(self):
        await self.connect_pool()
        return await self.pool.llen(self.name)

    async def empty(self):
        await self.connect_pool()
        length = await self.size()
        return length == 0

    async def get(self):
        await self.connect_pool()
        raw_data = await self.pool.rpop(self.name)
        return self.loads_msg(raw_data)

    def dumps_msg(self, msg=None):
        if msg is None:
            return ''
        return pickle.dumps(msg)

    def loads_msg(self, msg=None):
        if msg is None:
            return None
        return pickle.loads(msg)
