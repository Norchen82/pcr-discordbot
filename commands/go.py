import discord
from module import msg
import re


async def do_command(ctx: discord.Interaction, value: str, desc: str = ""):
    """
    @deprecated
    Retrieve the boss remaining health points from the latest message in the channel,
    subtract the estimated damage points, and send the result to the user.
    """
    try:
        # If the estimated damage does not start with minus symbol, insert one at the beginning.
        estimated_damage = value.strip()
        if not estimated_damage.startswith("-"):
            estimated_damage = "-" + estimated_damage

        if not re.match(r"\-\d+", estimated_damage):
            raise Exception("Invalid estimated damage.")

        await ctx.response.send_message(
            f"go指令已棄用，請直接在報刀區輸入「{estimated_damage}」。",
            ephemeral=True,
            delete_after=5,
        )
    except Exception:
        await msg.reply_error(ctx, "預估傷害不正確。")
