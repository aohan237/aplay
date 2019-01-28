from asyncnsq import create_reader
from asyncnsq import create_writer
from aplay.kernel.actor import Actor
from aplay.kernel.system import KernelActor
from aplay.kernel.logger import actor_logger
import asyncio


class MessageActor(Actor):

    async def msg_handler(self, msg=None):
        if not hasattr(self, 'nsq_writer'):
            self.nsq_writer = await create_writer(host='127.0.0.1', port=4150,
                                                  heartbeat_interval=30000,
                                                  feature_negotiation=True,
                                                  tls_v1=True,
                                                  snappy=False,
                                                  deflate=False,
                                                  deflate_level=0,
                                                  loop=self.loop)

        result = await self.nsq_writer.pub('new', msg.body)
        actor_logger.info(f'nsq_msg_handler,{msg},{result}')
        await msg.fin()

    def aa(self, *args, **kwargs):
        print('\n\ncallback', args, kwargs)


class NsqKernelActor(KernelActor):
    async def msg_handler(self, msg=None):
        nsqd_tcp_addresses = msg.get(
            'nsqd_tcp_addresses', ['127.0.0.1:4150'])
        max_in_flight = msg.get('max_in_flight', 200)
        topic = msg.get('topic')
        channel = msg.get('channel')
        reader = await create_reader(
            nsqd_tcp_addresses=nsqd_tcp_addresses,
            max_in_flight=max_in_flight)
        await reader.subscribe(topic, channel)
        msg_actor = self.create_actor('msg', actor_cls=MessageActor)
        async for message in reader.messages():
            msg_actor.send(message)


bb = NsqKernelActor("nsq")
loop = asyncio.get_event_loop()
loop.create_task(
    bb.send({
        "nsqd_tcp_addresses": ['127.0.0.1:4150'],
        "max_in_flight": 200,
        "topic": 'test_async_nsq',
        "channel": 'nsq',
    })
)
bb.start()
