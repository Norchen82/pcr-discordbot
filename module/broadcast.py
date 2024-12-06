import discord
from libs.mongo import db


class BroadcastTarget:
    def __init__(self, target_type: str, guild_id: int, channel_id: int):
        self.target_type = target_type
        self.guild_id = guild_id
        self.channel_id = channel_id


def add_channel(guild_id: int, channel_id: int):
    """
    將指定的頻道加入廣播對象列表內
    """
    if db is None:
        raise Exception("Connection to database failed.")

    targets = [
        target
        for target in db.broadcastTargets.find(
            {"targetType": "textChannel", "guildId": guild_id, "channelId": channel_id}
        )
    ]
    if len(targets) > 0:
        return

    db.broadcastTargets.insert_one(
        {"targetType": "textChannel", "guildId": guild_id, "channelId": channel_id}
    )


def delete_channel(guild_id: int, channel_id: int):
    """
    將指定的頻道從廣播對象列表中移除
    """
    if db is None:
        raise Exception("Connection to database failed.")

    db.broadcastTargets.delete_one(
        {"targetType": "textChannel", "guildId": guild_id, "channelId": channel_id}
    )


def get_broadcast_targets() -> list[BroadcastTarget]:
    """
    取得廣播對象列表
    """
    if db is None:
        raise Exception("Connection to database failed.")

    return [
        BroadcastTarget(
            target_type=target["targetType"],
            guild_id=target["guildId"],
            channel_id=target["channelId"],
        )
        for target in db.broadcastTargets.find()
    ]


async def broadcast(client: discord.Client, message: str):
    targets = get_broadcast_targets()
    for target in targets:
        try:
            channel = client.get_guild(target.guild_id).get_channel(target.channel_id)
            await channel.send(content=message)
        except:
            pass
