import discord
from module import cfg
import urllib.parse


class GenPicModal(discord.ui.Modal, title="產生隊伍角色圖片"):
    def __init__(self):
        self.timeline = discord.ui.TextInput[GenPicModal](
            label="時間軸",
            placeholder="請輸入時間軸",
            required=True,
            style=discord.TextStyle.paragraph,
        )

    async def on_submit(self, interaction: discord.Interaction):
        tl = urllib.parse.quote(self.timeline.value)
        url = f"[隊伍圖片連結]({cfg.website_url()}?tl={tl})"
        await interaction.response.send_message(url, ephemeral=True)

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        await interaction.response.send_message(
            "發生錯誤，請聯繫管理員", ephemeral=True
        )

        print(error)


async def do_command(ctx: discord.Interaction):
    await ctx.response.send_modal(GenPicModal())
