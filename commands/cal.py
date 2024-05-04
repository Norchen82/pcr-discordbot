import discord
from module import cal, msg


async def do_command(ctx: discord.Interaction, expr: str, desc: str = ""):
    """
    Calculate the expression and send the result to the user.
    """
    try:
        result = cal.compile(expr)
        message = f"{expr}={result} {desc}".strip()
        await msg.reply_with_message(ctx, message)
    except Exception as ex:
        print(f"expr={expr}, desc={desc}, ex={ex}")
        await ctx.response.send_message(
            f'"{expr}"不是一個有效的運算式。', ephemeral=True, delete_after=5
        )
