from discord import app_commands
import discord
from discord import app_commands
from module import cfg
from bot import client
from commands import (
    broadcast_add,
    broadcast_list,
    broadcast_rm,
    broadcast,
    cal,
    go,
    history,
    img,
    rm,
)

tree = app_commands.CommandTree(client)

role_choices: list[app_commands.Choice[str]] = []


async def init() -> int:
    global role_choices
    for clan in cfg.clans():
        role_choices.append(
            app_commands.Choice(name=clan.role_name, value=str(clan.role_id))
        )

    cmds = await tree.sync(guild=discord.Object(id=cfg.guild_id()))
    return len(cmds)


@tree.command(
    name="broadcast_add",
    description="綁定廣播頻道（此指令只有管理員可以使用）",
    guild=discord.Object(id=cfg.guild_id()),
)
@app_commands.describe(channel="要被廣播訊息的頻道")
@app_commands.rename(channel="頻道")
async def command_broadcast_add(
    interaction: discord.Interaction, channel: discord.TextChannel
):
    try:
        await broadcast_add.do_command(interaction, channel)
    except Exception:
        await interaction.response.edit_message(
            content="發生錯誤", view=None, delete_after=5
        )


@tree.command(
    name="broadcast_list",
    description="列出廣播頻道清單（此指令只有管理員可以使用）",
    guild=discord.Object(id=cfg.guild_id()),
)
async def command_broadcast_list(interaction: discord.Interaction):
    try:
        await broadcast_list.do_command(interaction)
    except Exception:
        await interaction.response.edit_message(
            content="發生錯誤", view=None, delete_after=5
        )


@tree.command(
    name="broadcast_rm",
    description="移除廣播頻道（此指令只有管理員可以使用）",
    guild=discord.Object(id=cfg.guild_id()),
)
@app_commands.describe(channel="要被從清單中移除的頻道")
@app_commands.rename(channel="頻道")
async def command_broadcast_rm(
    interaction: discord.Interaction, channel: discord.TextChannel
):
    try:
        await broadcast_rm.do_command(interaction, channel)
    except Exception:
        await interaction.response.edit_message(
            content="發生錯誤", view=None, delete_after=5
        )


@tree.command(
    name="broadcast",
    description="向綁定的頻道廣播訊息（此指令只有管理員可以使用）",
    guild=discord.Object(id=cfg.guild_id()),
)
@app_commands.describe(message="廣播的訊息內容")
@app_commands.rename(message="訊息內容")
async def command_broadcast(interaction: discord.Interaction, message: str):
    try:
        await broadcast.do_command(interaction, message)
    except Exception:
        await interaction.response.edit_message(
            content="發生錯誤", view=None, delete_after=5
        )


@tree.command(
    name="cal",
    description="簡易計算機，支援四則運算",
    guild=discord.Object(id=cfg.guild_id()),
)
@app_commands.describe(
    expr="請輸入數學算式，不要包含等號。例如:24000-4800",
    desc="請輸入想在運算結果後面的附加訊息。例如:等合",
)
@app_commands.rename(expr="運算式", desc="附加訊息")
async def command_cal(interaction: discord.Interaction, expr: str, desc: str = ""):
    try:
        await cal.do_command(interaction, expr, desc)
    except Exception:
        await interaction.response.edit_message(
            content="發生錯誤", view=None, delete_after=5
        )


@tree.command(
    name="go",
    description="【已棄用】請直接在報刀區輸入預估傷害。",
    guild=discord.Object(id=cfg.guild_id()),
)
@app_commands.describe(
    value="請輸入你本次出刀預估的傷害量。",
    desc="請輸入想在運算結果後面的附加訊息。例如:等合",
)
@app_commands.rename(value="預估傷害", desc="附加訊息")
async def command_go(interaction: discord.Interaction, value: str, desc: str = ""):
    try:
        await go.do_command(interaction, value, desc)
    except Exception:
        await interaction.response.edit_message(
            content="發生錯誤", view=None, delete_after=5
        )


@tree.command(
    name="history",
    description="查看指定日期各戰隊成員在報刀區的總留言數。（警告：此功能測試中，不保證運作正確）",
    guild=discord.Object(id=cfg.guild_id()),
)
@app_commands.describe(role="要查詢的戰隊", datestr="要查詢的日期，格式:yyyy-mm-dd")
@app_commands.rename(role="戰隊", datestr="日期")
@app_commands.choices(role=role_choices)
async def command_history(
    interaction: discord.Interaction, role: app_commands.Choice[str], datestr: str
):
    try:
        await history.do_command(interaction, role, datestr)
    except Exception:
        await interaction.response.edit_message(
            content="發生錯誤", view=None, delete_after=5
        )


@tree.command(
    name="img",
    description="根據傳入的時間軸，產生隊伍角色的圖片。",
    guild=discord.Object(id=cfg.guild_id()),
)
async def command_img(interaction: discord.Interaction):
    try:
        await img.do_command(interaction)
    except Exception:
        await interaction.response.edit_message(
            content="發生錯誤", view=None, delete_after=5
        )


@tree.command(
    name="rm",
    description="【報刀用指令】刪除你本週次出的最後一個刀。",
    guild=discord.Object(id=cfg.guild_id()),
)
async def command_rm(interaction: discord.Interaction):
    try:
        await rm.do_command(interaction)
    except Exception:
        await interaction.response.edit_message(
            content="發生錯誤", view=None, delete_after=5
        )
