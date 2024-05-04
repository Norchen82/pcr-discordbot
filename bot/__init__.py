from typing import Awaitable, Callable
from discord import Client, Intents
import discord
from module import cfg, msg, atkcheckin

# 機器人的意圖
intents = Intents.default()
intents.message_content = True
intents.members = True

# 機器人客戶端
client = Client(intents=intents)

# 註冊指令的初始化函式
_register_commands: Callable[[], Awaitable[int]] | None = None


def init(register_commands: Callable[[], Awaitable[int]]):
    """
    初始化機器人
    """
    global _register_commands
    _register_commands = register_commands


def client_id() -> int:
    """
    取得機器人的客戶端ID(即Discord中的User ID)
    """
    if client.user is None:
        raise Exception("The client is not ready yet.")

    return client.user.id


@client.event
async def on_ready():
    """
    執行`client.run()`後，當機器人載入完畢時，會執行此函式
    """

    if _register_commands is not None:
        print("Registering commands...")
        cmd_count = await _register_commands()
        print(f"{cmd_count} commands registered.")

    print(f"Logged on as {client.user}")


@client.event
async def on_message(message: discord.Message):
    try:
        if message.author == client.user:
            return

        # 如果非報刀區的頻道，就不處理
        if cfg.boss_health(message.channel.id) == None:
            return

        # 如果非文字頻道，就不處理
        if not isinstance(message.channel, discord.TextChannel):
            return

        # 將訊息以行為單位進行處理
        message_lines = message.content.split("\n")

        # 如果是報刀訊息，就進行報刀動作
        if atkcheckin.is_command(message_lines):
            option = atkcheckin.AttackCheckinOption(
                command_lines=message_lines,
                command_id=message.id,
                caller_id=message.author.id,
                boss_id=message.channel.id,
            )
            reader = msg.DiscordTextChannelReader(message.channel)
            writer = msg.DiscordMessageWriter(message)
            await atkcheckin.do_command(option=option, reader=reader, writer=writer)

    except Exception as ex:
        print(ex)
        pass
