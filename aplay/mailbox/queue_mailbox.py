from asyncio.queues import Queue
from .base import MailBox


class QueueMailBox(MailBox):
    def __init__(self, *args, **kwargs):
        super(QueueMailBox, self).__init__(*args, **kwargs)
        self.queue = Queue()

    async def put(self, msg=None):
        self.queue.put_nowait(msg)

    async def size(self):
        return self.queue.qsize()

    async def empty(self):
        return self.queue.empty()

    async def get(self):
        result = None
        result = await self.queue.get()
        return result
