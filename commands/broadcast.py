import discord
from module import perm, broadcast, msg
from bot import client
from discord.ui import Button


async def confirm_broadcast(ctx: discord.Interaction, message: str):
    await ctx.delete_original_response()
    await broadcast.broadcast(client, message)


async def cancel_broadcast(ctx: discord.Interaction):
    await ctx.delete_original_response()


async def do_command(ctx: discord.Interaction, message: str):
    try:
        if not perm.is_admin(ctx.user.id):
            await ctx.response.send_message(
                content="你沒有權限使用此指令", ephemeral=True
            )
            return

        targets = broadcast.get_broadcast_targets()
        if len(targets) == 0:
            await ctx.response.send_message(
                "目前廣播指令尚未綁定任何頻道，請先使用**/broadcast_add**指令來綁定頻道。",
                ephemeral=True,
            )
            return

        view = discord.ui.View()

        confirm_button = Button[discord.ui.View](
            style=discord.ButtonStyle.green,
            label="確認",
            custom_id="confirm",
        )
        confirm_button.callback = lambda interaction: confirm_broadcast(ctx, message)
        view.add_item(confirm_button)

        cancel_button = Button[discord.ui.View](
            style=discord.ButtonStyle.red,
            label="取消",
            custom_id="cancel",
        )
        cancel_button.callback = lambda interaction: cancel_broadcast(ctx)
        view.add_item(cancel_button)

        channel_names = ""
        for target in targets:
            guild = client.get_guild(target.guild_id)
            if guild is None:
                continue

            channel = guild.get_channel(target.channel_id)
            if channel is None:
                continue

            channel_names += channel.name + "\n"

        await ctx.response.send_message(
            content=f"即將發送廣播訊息：\n```\n{message}\n```\n給以下 **{len(targets)}** 個頻道：\n```{channel_names}```\n請確認是否繼續：",
            view=view,
            ephemeral=True,
        )

    except Exception as ex:
        print(ex, flush=True)
        await msg.reply_error(ctx, "發生未知錯誤")
