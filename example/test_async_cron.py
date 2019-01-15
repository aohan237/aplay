from aplay.kernel.system import KernelActor
from async_cron.schedule import Scheduler
from async_cron.job import CronJob


class SchedulerKernel(KernelActor):

    def __init__(self, *args, **kwargs):
        super(SchedulerKernel, self).__init__(*args, **kwargs)
        self.sch = Scheduler()

    async def msg_handler(self, msg=None):
        await self.sch.start()


async def test(*args, **kwargs):
    print(args, kwargs)


def tt(*args, **kwargs):
    print(args, kwargs)


myjob = CronJob(name='test').every(5).second.go(test, (1, 2, 3), name=123)
job2 = CronJob(name='tt', tolerance=100).every().at(
    "2019-01-15 16:12").go(tt, (5), age=99)

bb = SchedulerKernel()
bb.sch.add_job(myjob)
bb.sch.add_job(job2)
bb.send("hahaha")
bb.start()
