import bot
from datetime import datetime, timedelta
from typing import Any, Coroutine
from cronjobs.jjc_notify import on_jjc_notify
from cronjobs.clan_battle_notify import on_clan_battle_notify


class CronJob:
    def __init__(
        self,
        name: str,
        interval: int,
        coroutine: Coroutine[Any, Any, None],
    ):
        self.name = name
        self.interval = interval
        self.coroutine = coroutine

        self.next_run = datetime.now() + timedelta(seconds=interval)

    async def run(self):
        await self.coroutine
        self.next_run = datetime.now() + timedelta(seconds=self.interval)


jobs: list[CronJob] = [
    CronJob("jjc_notify", 180, on_jjc_notify()),
    CronJob("clan_battle_notify", 60, on_clan_battle_notify()),
]


async def loop_action():
    for job in jobs:
        if job.next_run < datetime.now():
            await job.run()


bot.coroutine_loop_action = loop_action
