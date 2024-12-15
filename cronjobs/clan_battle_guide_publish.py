"""
排程：發布戰隊戰攻略
"""

import io
import discord
from bot import client
from module.clanbattle.guidereleasejob import (
    fetch_job,
    close_job,
    get_team_sheet,
    DiscordReleaseJob,
    DiscordMessageReceiver,
    ClanBattleBoss,
)


class MessageReceiver:
    def __init__(
        self, job: DiscordReleaseJob, receiver: DiscordMessageReceiver, boss_index: int
    ):
        self.job = job
        self.receiver = receiver
        self.boss_index = boss_index

        guild = client.get_guild(job.guildId)
        if guild is None:
            raise Exception("Guild not found")
        self.guild = guild

        channel = self.guild.get_channel(job.channelId)
        if channel is None or not isinstance(channel, discord.TextChannel):
            raise Exception("Channel not found")
        self.channel = channel

    async def init(self):
        self.thread = None
        if self.receiver.threadId is not None:
            thread = self.channel.get_thread(self.receiver.threadId)
            if thread is not None:
                self.thread = thread

                if self.receiver.imageMessageId1 is not None:
                    self.image_message_1 = await self.channel.fetch_message(
                        self.receiver.imageMessageId1
                    )

                if self.receiver.imageMessageId2 is not None:
                    self.image_message_2 = await self.thread.fetch_message(
                        self.receiver.imageMessageId2
                    )

                if self.receiver.timelineMessageId1 is not None:
                    self.timeline_message_1 = await self.thread.fetch_message(
                        self.receiver.timelineMessageId1
                    )

                if self.receiver.timelineMessageId2 is not None:
                    self.timeline_message_2 = await self.thread.fetch_message(
                        self.receiver.timelineMessageId2
                    )

                if self.receiver.timelineMessageId3 is not None:
                    self.timeline_message_3 = await self.thread.fetch_message(
                        self.receiver.timelineMessageId3
                    )

    def get_thread_name(self):
        if self.boss_index == 0:
            return "一王半自動"
        elif self.boss_index == 1:
            return "二王半自動"
        elif self.boss_index == 2:
            return "三王半自動"
        elif self.boss_index == 3:
            return "四王半自動"
        else:
            return "五王半自動"

    async def create_thread(self):
        thread_name = self.get_thread_name()

        first_image = await self.channel.send("** **")
        self.thread = await self.channel.create_thread(
            name=thread_name, message=first_image
        )

        self.image_message_1 = first_image

        second_image = await self.thread.send("** **")
        self.image_message_2 = second_image

        timeline_message_1 = await self.thread.send("** **")
        self.timeline_message_1 = timeline_message_1

        timeline_message_2 = await self.thread.send("** **")
        self.timeline_message_2 = timeline_message_2

        timeline_message_3 = await self.thread.send("** **")
        self.timeline_message_3 = timeline_message_3

    async def publish_image_1(self, content: bytes | None):
        if self.thread is None:
            await self.create_thread()

        if content is None:
            await self.image_message_1.edit(content="** **")
            return

        fp = io.BytesIO(content)
        await self.image_message_1.edit(
            content="", attachments=[discord.File(fp=fp, filename="team_sheet.png")]
        )

    async def publish_image_2(self, content: bytes | None):
        if self.thread is None:
            await self.create_thread()

        if content is None:
            await self.image_message_2.edit(content="** **")
            return

        fp = io.BytesIO(content)
        await self.image_message_2.edit(
            content="", attachments=[discord.File(fp=fp, filename="team_sheet.png")]
        )

    async def publish_timeline_1(self, content: str | None):
        if self.thread is None:
            await self.create_thread()

        if content is None or content.strip() == "":
            await self.timeline_message_1.edit(content="** **")
            return

        await self.timeline_message_1.edit(content=content)

    async def publish_timeline_2(self, content: str | None):
        if self.thread is None:
            await self.create_thread()

        if content is None or content.strip() == "":
            await self.timeline_message_2.edit(content="** **")
            return

        await self.timeline_message_2.edit(content=content)

    async def publish_timeline_3(self, content: str | None):
        if self.thread is None:
            await self.create_thread()

        if content is None or content.strip() == "":
            await self.timeline_message_3.edit(content="** **")
            return

        await self.timeline_message_3.edit(content=content)

    def to_message(self):
        return DiscordMessageReceiver(
            threadId=self.thread.id if self.thread is not None else None,
            imageMessageId1=self.image_message_1.id,
            imageMessageId2=self.image_message_2.id,
            timelineMessageId1=self.timeline_message_1.id,
            timelineMessageId2=self.timeline_message_2.id,
            timelineMessageId3=self.timeline_message_3.id,
        )


async def on_clan_battle_guide_publish():
    job = await fetch_job()
    if job is None:
        return

    message_store = init_message_store(job)
    for boss_index, boss in enumerate(job.clanBattle.bosses):
        receiver = get_receiver(job, message_store, boss, boss_index)
        await receiver.init()

        team_sheet_1 = await get_team_sheet(job, boss, 0)
        await receiver.publish_image_1(team_sheet_1)

        team_sheet_2 = await get_team_sheet(job, boss, 5)
        await receiver.publish_image_2(team_sheet_2)

        await receiver.publish_timeline_1(build_timeline_content(job, boss, 0))
        await receiver.publish_timeline_2(build_timeline_content(job, boss, 3))
        await receiver.publish_timeline_3(build_timeline_content(job, boss, 6))

        message_store[boss.id] = receiver.to_message()
        break

    await close_job(job.id, message_store)


def init_message_store(job: DiscordReleaseJob):
    message_store: dict[str, DiscordMessageReceiver] = {}
    if job.receivers is not None:
        message_store = job.receivers

    return message_store


def get_receiver(
    job: DiscordReleaseJob,
    message_store: dict[str, DiscordMessageReceiver],
    boss: ClanBattleBoss,
    boss_index: int,
) -> MessageReceiver:
    if boss.id in message_store:
        return MessageReceiver(job, message_store[boss.id], boss_index)

    return MessageReceiver(
        job,
        DiscordMessageReceiver(
            threadId=None,
            imageMessageId1=None,
            imageMessageId2=None,
            timelineMessageId1=None,
            timelineMessageId2=None,
            timelineMessageId3=None,
        ),
        boss_index,
    )


def build_timeline_content(
    job: DiscordReleaseJob, boss: ClanBattleBoss, start_index: int
) -> str:
    guides = [
        guide
        for guide in job.guides
        if guide.boss is not None and guide.boss.id == boss.id
    ]

    guides = guides[start_index : start_index + 3]

    # 將所有攻略的時間軸合併成一個字串
    timeline_messages = "\n\n----------\n\n".join(
        [guide.timeline for guide in guides if guide.timeline.strip() != ""]
    )

    return timeline_messages
