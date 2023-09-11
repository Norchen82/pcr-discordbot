"""
This module contains functions to interact with Discord message system.
"""

import discord
from discord import Member, User

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
    
def mention(user: User|Member):
    """
    Get the syntax for mentioning the specified user.
    """
    return f"<@{user.id}>"