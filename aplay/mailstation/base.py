import uuid


class MailStation:
    def __init__(self, *args, **kwargs):
        self._name = kwargs.get("name", str(uuid.uuid1()))
        self._ready = False

    async def ready(self):
        return self._ready

    async def register_address(self):
        raise NotImplementedError

    async def check_address(self, address=None):
        raise NotImplementedError

    async def send_to_address(self, address=None, msg=None):
        raise NotImplementedError

    async def get_mailbox(self, address):
        raise NotImplementedError

    async def get_address_actors(self, address):
        raise NotImplementedError
