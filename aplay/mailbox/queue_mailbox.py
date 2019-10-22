from .base import MailBox
from asyncio.queues import Queue
import psutil
import logging
logger = logging.getLogger(__package__)


class QueueMailBox(MailBox):
    def __init__(self, *args, **kwargs):
        super(QueueMailBox, self).__init__(*args, **kwargs)
        self._queue = Queue()
        self._ready = True

    async def prepare(self):
        self._ready = True

    async def put(self, msg=None):
        if await self.policy():
            self._queue.put_nowait(msg)

    async def size(self):
        return self._queue.qsize()

    async def empty(self):
        return self._queue.empty()

    async def get(self):
        result = None
        result = await self._queue.get()
        return result

    async def policy(self):
        mem_percent = psutil.virtual_memory().percent
        if mem_percent > 80:
            logger.warning('memory usage is gt than 80')
        return True
