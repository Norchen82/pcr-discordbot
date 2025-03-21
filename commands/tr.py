import discord
from module import tr


class TimelineAdjustModal(discord.ui.Modal, title="文字軸補償秒數轉換"):
    remaining_time = discord.ui.TextInput(
        label="剩餘秒數",
        placeholder="請輸入剩餘秒數",
        required=True,
        style=discord.TextStyle.short,
    )

    timeline = discord.ui.TextInput(
        label="時間軸",
        placeholder="請輸入時間軸",
        required=True,
        style=discord.TextStyle.paragraph,
    )

    async def on_submit(self, interaction: discord.Interaction):
        result = tr.adjust_timeline(self.remaining_time.value, self.timeline.value)

        if result != "":
            await interaction.response.send_message(
                f"""
秒數：{tr.format_time(tr.get_time(tr.parse_time(self.remaining_time.value)), ":")}
原文字軸：
```cs
{self.timeline.value}
```
轉換結果：
```cs
{result}
```
"""
            )
        else:
            await interaction.response.send_message("轉換結果已經為空")

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        await interaction.response.send_message(
            "發生錯誤，請聯繫管理員", ephemeral=True
        )

        print(error)


async def do_command(ctx: discord.Interaction):
    await ctx.response.send_modal(TimelineAdjustModal())
