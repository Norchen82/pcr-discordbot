import discord
from module import perm, broadcast


async def do_command(ctx: discord.Interaction, channel: discord.TextChannel):
    try:
        if not perm.is_admin(ctx.user.id):
            await ctx.response.send_message(
                content="你沒有權限使用此指令", ephemeral=True
            )
            return

        broadcast.add_channel(channel.guild.id, channel.id)
        await ctx.response.send_message(
            content=f"{channel.name} 已成功加入廣播清單", ephemeral=True
        )
    except Exception as ex:
        print(ex, flush=True)
        await ctx.response.send_message(content="發生錯誤", ephemeral=True)
