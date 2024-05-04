import discord
from module import perm, broadcast
from bot import client


async def do_command(ctx: discord.Interaction):
    try:
        if not perm.is_admin(ctx.user.id):
            await ctx.response.send_message(
                content="你沒有權限使用此指令", ephemeral=True
            )
            return

        channel_names = ""

        targets = broadcast.get_broadcast_targets()
        for target in targets:
            guild = client.get_guild(target.guild_id)
            if guild is None:
                continue

            channel = guild.get_channel(target.channel_id)
            if channel is None:
                continue

            channel_names += channel.name + "\n"

        if channel_names == "":
            await ctx.response.send_message(
                content="目前廣播指令尚未綁定任何頻道", ephemeral=True
            )
        else:
            await ctx.response.send_message(
                content=f"目前綁定的頻道有：\n{channel_names}", ephemeral=True
            )
    except Exception as ex:
        print(ex, flush=True)
        await ctx.response.send_message(content="發生錯誤", ephemeral=True)
