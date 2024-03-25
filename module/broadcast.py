import pymongo
import os
import urllib
import discord

host = os.getenv("MONGO_HOST")
port = os.getenv("MONGO_PORT")
user_name = os.getenv("MONGO_INITDB_ROOT_USERNAME")
password = os.getenv("MONGO_INITDB_ROOT_PASSWORD")

client = pymongo.MongoClient(f'mongodb://{user_name}:{urllib.parse.quote_plus(password)}@{host}:{port}')
db = client.bot

def add_channel(guild_id: int, channel_id: int):
    """
    將指定的頻道加入廣播對象列表內
    """
    targets = [target for target in db.broadcastTargets.find({"targetType": "textChannel", "guildId": guild_id, "channelId": channel_id})]
    if len(targets) > 0:
        return
    
    db.broadcastTargets.insert_one({"targetType": "textChannel", "guildId": guild_id, "channelId": channel_id})

def delete_channel(guild_id: int, channel_id: int):
    """
    將指定的頻道從廣播對象列表中移除
    """
    db.broadcastTargets.delete_one({"targetType": "textChannel", "guildId": guild_id, "channelId": channel_id})

def get_broadcast_targets():
    """
    取得廣播對象列表
    """
    return [target for target in db.broadcastTargets.find()]

async def broadcast(client: discord.Client, message: str):
    targets = get_broadcast_targets()
    for target in targets:
        try:
            channel = client.get_guild(target["guildId"]).get_channel(target["channelId"])
            await channel.send(content=message)
        except:
            pass