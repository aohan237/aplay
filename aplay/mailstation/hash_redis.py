from collections import defaultdict
import weakref
from .base import MailStation
from aplay.mailbox.redis_box import RedisQueueMailBox
import aioredis
import uuid

import logging

logger = logging.getLogger(__package__)


class HashRedisMailStation(MailStation):
    def __init__(self, station_address=None, **kwargs):
        self._name = kwargs.get("name", str(uuid.uuid1()))
        self._ready = False
        self._station_address = station_address
        self._address_book = {}
        self._address_actors = defaultdict(list)
        self._pool = aioredis.from_url(self._station_address)

    async def ready(self):
        return self._ready

    async def prepare(self):
        pass

    def new_mail_box(self, name=None):
        mailbox = RedisQueueMailBox(pool=self._pool, name=name)
        return mailbox

    def register_address(self, address=None, actor=None):
        mailbox = self.new_mail_box(name=address)
        self._address_book[address] = mailbox
        self._address_actors[address].append(actor)
        return mailbox

    async def check_address(self, address):
        return address in self._address_book

    async def get_mailbox(self, address):
        return self._address_book.get(address)

    async def send_to_address(self, address, msg):
        mailbox = self._address_book.get(address)
        if mailbox is None:
            return False
        return await mailbox.put(msg)

    async def get_address_actors(self, address):
        return self._address_actors.get(address)
