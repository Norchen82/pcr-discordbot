"""
This module contains functions to interact with Discord message system.
"""

import re
import discord
from discord import Member, User

# The time for the error message to live
ERROR_DISPLAY_TIME = 5


async def reply_with_message(ctx: discord.Interaction, content: str):
    """
    Reply to the user's command with a standard message.
    This is intended to make the channel look cleaner because the orignial interaction message includes extra information such as "<who> used <command>"
    """
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
    await ctx.response.send_message(content, ephemeral=True, delete_after=ERROR_DISPLAY_TIME)


def mention(user: User|Member):
    """
    Get the syntax for mentioning the specified user.
    """
    return f"<@{user.id}>"


async def last_message(ctx: discord.Interaction):
    if ctx.channel.last_message != None:
        return ctx.channel.last_message
    
    histories = [history async for history in ctx.channel.history(limit=1)]
    if len(histories) == 0:
        return None
    return histories[0]


def is_round_divider(message: str):
    pattern = r"^(=|-)+\s*\d*\s*(=|-)+$"
    return re.match(pattern, message)