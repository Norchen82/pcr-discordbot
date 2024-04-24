"""
This module contains functions to interact with Discord message system.
"""

import re
import discord
import pytz

# The time for the error message to live
ERROR_DISPLAY_TIME = 5


class TextMessage:
    def __init__(self, content: str, id: int, author_id: int, channel_id: int):
        self.content = content
        self.id = id
        self.author_id = author_id
        self.channel_id = channel_id


class MessageWriter:
    async def write(
        self, content: str, mention: int | None = None, silent: bool = False
    ) -> TextMessage:
        raise NotImplementedError

    async def delete(self) -> None:
        raise NotImplementedError

    async def delete_by_id(self, id: int) -> None:
        raise NotImplementedError


class DiscordMessageWriter(MessageWriter):
    def __init__(self, message: discord.Message):
        self.message = message

    async def write(
        self, content: str, mention: int | None = None, silent: bool = False
    ) -> TextMessage:
        if mention != None:
            content = f"<@{mention}> {content}"

        new_message = await self.message.channel.send(content, silent=silent)
        return TextMessage(
            content=content,
            id=new_message.id,
            author_id=new_message.author.id,
            channel_id=new_message.channel.id,
        )

    async def delete(self):
        if type(self.message.channel) != discord.TextChannel:
            return

        channel_name = self.message.channel.name
        author_name = self.message.author.display_name
        content = self.message.content
        created_at = self.message.created_at.astimezone(pytz.timezone("Asia/Taipei"))
        await self.message.delete()
        print(
            f"[刪除訊息]\n頻道：{channel_name}\n發送人：{author_name}\n內容：{content}\n發送時間：{created_at}"
        )

    async def delete_by_id(self, id: int):
        message = await self.message.channel.fetch_message(id)
        await message.delete()


class DiscordTextChannelWriter(MessageWriter):
    def __init__(self, channel: discord.TextChannel):
        self.channel = channel

    async def write(
        self, content: str, mention: int | None = None, silent: bool = False
    ) -> TextMessage:
        if mention != None:
            content = f"<@{mention}> {content}"

        new_message = await self.channel.send(content, silent=silent)
        return TextMessage(
            content=content,
            id=new_message.id,
            author_id=new_message.author.id,
            channel_id=new_message.channel.id,
        )

    async def delete(self) -> None:
        pass

    async def delete_by_id(self, id: int) -> None:
        message = await self.channel.fetch_message(id)
        await message.delete()


class MessageReader:
    async def read_all(self, limit: int) -> list[TextMessage]:
        raise NotImplementedError


class DiscordTextChannelReader(MessageReader):
    def __init__(self, channel: discord.TextChannel):
        self.channel = channel

    async def read_all(self, limit: int) -> list[TextMessage]:
        return [
            TextMessage(
                content=history.content,
                id=history.id,
                author_id=history.author.id,
                channel_id=history.channel.id,
            )
            async for history in self.channel.history(limit=10)
        ]


async def reply_with_message(ctx: discord.Interaction, content: str):
    """
    Reply to the user's command with a standard message.
    This is intended to make the channel look cleaner because the orignial interaction message includes extra information such as "<who> used <command>"
    """
    if type(ctx.channel) != discord.TextChannel:
        raise Exception("此指令只允許在文字頻道中執行。")

    mention_user = mention(ctx.user)
    message = f"{mention_user} {content}"

    # Send an empty message and delete it instantly, so the user won't see any message
    await ctx.response.send_message(content="** **", ephemeral=True, delete_after=0)

    # Send the calculation result with normal message
    await ctx.channel.send(content=message, silent=True)


async def reply_error(ctx: discord.Interaction, error_message: str):
    """
    Provide the error message to the user.
    (Only the user who initiated the interaction will be able to see the error message.)
    """
    if error_message == "":
        error_message = "發生未預期錯誤。"

    content = f"[錯誤] {error_message}"
    await ctx.response.send_message(
        content, ephemeral=True, delete_after=ERROR_DISPLAY_TIME
    )


def mention(user: discord.User | discord.Member):
    """
    Get the syntax for mentioning the specified user.
    """
    return f"<@{user.id}>"


async def get_round_lines(
    reader: MessageReader, ignores: list[str] = []
) -> list[str] | None:
    """
    取得本周次的所有報刀訊息行。
    """
    round_lines = None

    messages = [history for history in await reader.read_all(limit=20)]
    break_all = False

    for message in messages:
        lines = message.content.split("\n")
        lines.reverse()
        for index, line in enumerate(lines):
            true_index = len(lines) - index - 1
            if True in [f"{message.id}_{true_index}" == ignore for ignore in ignores]:
                continue

            line = line.strip()
            if is_round_divider(line):
                if round_lines == None:
                    round_lines = []
                break_all = True
                break

            if line != "":
                if round_lines == None:
                    round_lines = [line]
                else:
                    round_lines.append(line)
        if break_all:
            break

    # 因為是從最新的訊息開始往前找，所以要將找到的訊息行反轉過來
    if round_lines != None:
        round_lines.reverse()

    return round_lines


async def last_message(ctx: discord.Interaction):
    if type(ctx.channel) != discord.TextChannel:
        raise Exception("此指令只允許在文字頻道中執行。")

    if ctx.channel.last_message != None:
        return ctx.channel.last_message

    histories = [history async for history in ctx.channel.history(limit=1)]
    if len(histories) == 0:
        return None
    return histories[0]


def is_round_divider(message: str):
    pattern = r"^(=|-)+.*(=|-)+$"
    return re.match(pattern, message)
