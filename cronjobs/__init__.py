import bot
from datetime import datetime, timedelta
from typing import Any, Callable, Coroutine
from cronjobs.jjc_notify import on_jjc_notify
from cronjobs.clan_battle_notify import on_clan_battle_notify
from cronjobs.clan_battle_guide_publish import on_clan_battle_guide_publish


class CronJob:
    def __init__(
        self,
        name: str,
        interval: int,
        coroutine: Callable[[], Coroutine[Any, Any, None]],
        immediate: bool = False,
    ):
        self.name = name
        self.interval = interval
        self.coroutine = coroutine

        if immediate:
            self.next_run = datetime.now()
        else:
            self.next_run = datetime.now() + timedelta(seconds=interval)

    async def run(self):
        self.next_run = datetime.now() + timedelta(seconds=self.interval)
        await self.coroutine()
        self.next_run = datetime.now() + timedelta(seconds=self.interval)


jobs: list[CronJob] = [
    CronJob("jjc_notify", 180, on_jjc_notify),
    CronJob("clan_battle_notify", 60, on_clan_battle_notify, immediate=True),
    CronJob(
        "clan_battle_guide_publish", 60, on_clan_battle_guide_publish, immediate=True
    ),
]


async def loop_action():
    for job in jobs:
        if job.next_run < datetime.now():
            try:
                await job.run()
            except Exception as err:
                print(err)


bot.coroutine_loop_action = loop_action
