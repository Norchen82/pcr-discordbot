import os
import discord
from discord.ui import Button
from discord import app_commands
import module.cal as cal
import module.msg as msg
import module.broadcast as broadcast
import module.env as env
import module.perm as perm
import module.atkcheckin as atkcheckin
import re
from datetime import datetime, timedelta
import pytz
import urllib.parse

import commands.rm as rm

bot_token = os.getenv("BOT_TOKEN")
guild_id = os.getenv("GUILD_ID")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

guild = client.get_guild(int(guild_id))
role_choices: list = []


def init_role_choices():
    global role_choices
    for role in env.get_roles():
        role_choices.append(app_commands.Choice(name=role.name, value=role.id))


class History:
    def __init__(self, member_id: int, histories: list):
        self.member_id = member_id
        self.histories = histories


@client.event
async def on_ready():
    env.init(client)
    init_role_choices()

    await tree.sync(guild=discord.Object(id=guild_id))
    print(f"Logged on as {client.user}")


# 報刀佇列
queue = {}


@client.event
async def on_message(message: discord.Message):
    try:
        if message.author == client.user:
            return

        # 如果非報刀區的頻道，就不處理
        if env.get_boss_health(message.channel.id) == None:
            return

        # 將訊息以行為單位進行處理
        message_lines = message.content.split("\n")

        # 如果是報刀訊息，就進行報刀動作
        if atkcheckin.is_command(message_lines):
            option = atkcheckin.AttackCheckinOption(
                command_lines=message_lines,
                command_id=message.id,
                caller_id=message.author.id,
                boss_id=message.channel.id,
            )
            reader = msg.DiscordTextChannelReader(message.channel)
            writer = msg.DiscordMessageWriter(message)
            await atkcheckin.do_command(option=option, reader=reader, writer=writer)

    except Exception as ex:
        print(ex)
        pass


@tree.command(
    name="cal",
    description="簡易計算機，支援四則運算",
    guild=discord.Object(id=guild_id),
)
@app_commands.describe(
    expr="請輸入數學算式，不要包含等號。例如:24000-4800",
    desc="請輸入想在運算結果後面的附加訊息。例如:等合",
)
@app_commands.rename(expr="運算式", desc="附加訊息")
async def command_cal(ctx: discord.Interaction, expr: str, desc: str = ""):
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


@tree.command(
    name="go",
    description="【已棄用】請直接在報刀區輸入預估傷害。",
    guild=discord.Object(id=guild_id),
)
@app_commands.describe(
    value="請輸入你本次出刀預估的傷害量。",
    desc="請輸入想在運算結果後面的附加訊息。例如:等合",
)
@app_commands.rename(value="預估傷害", desc="附加訊息")
async def command_go(ctx: discord.Interaction, value: str, desc: str = ""):
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
    except Exception as ex:
        await msg.reply_error(ctx, "預估傷害不正確。")


@tree.command(
    name="rm",
    description="【報刀用指令】刪除你本週次出的最後一個刀。",
    guild=discord.Object(id=guild_id),
)
async def command_rm(itr: discord.Interaction):
    await rm.do_command(itr)


@tree.command(
    name="history",
    description="查看指定日期各戰隊成員在報刀區的總留言數。（警告：此功能測試中，不保證運作正確）",
    guild=discord.Object(id=guild_id),
)
@app_commands.describe(role="要查詢的戰隊", datestr="要查詢的日期，格式:yyyy-mm-dd")
@app_commands.rename(role="戰隊", datestr="日期")
@app_commands.choices(role=role_choices)
async def command_history(
    ctx: discord.Interaction, role: app_commands.Choice[str], datestr: str
):
    try:
        timezone_tw = pytz.timezone("ROC")
        date = datetime.strptime(datestr, "%Y-%m-%d").replace(tzinfo=timezone_tw)

        # Day refresh on 05:00 a.m. everyday
        begin_time = date + timedelta(hours=5)
        end_time = begin_time + timedelta(days=1)

        # Initialize member map
        drole = ctx.guild.get_role(int(role.value))

        histories = {}
        for member in drole.members:
            histories[member.id] = [0, 0, 0, 0, 0]

        histories[env.get_master_id()] = [0, 0, 0, 0, 0]

        for index in range(1, 6):
            channel_ids = os.getenv(f"BOSS{index}_CHANNEL").split(",")
            role_index = role_ids.index(role.value)

            channel = ctx.guild.get_channel(int(channel_ids[role_index]))
            h = [
                history
                async for history in channel.history(after=begin_time, before=end_time)
            ]
            for history in h:
                member_id = history.author.id
                if member_id == client.user.id:
                    matches = re.findall(r"<@\d+>", history.content)
                    match = str(matches[0])

                    member_id = int(match[2:-1])

                histories[member_id][index - 1] += 1

        hl = []
        for key in histories:
            hl.append(History(member_id=key, histories=histories[key]))
        hl = sorted(hl, key=lambda x: sum(x.histories), reverse=True)

        embed = discord.Embed(title=f"{datestr} {role.name}成員出刀紀錄")
        body = ""
        for h in hl:
            member = ctx.guild.get_member(h.member_id)

            total = 0
            body += f"**{member.display_name}** : "
            for index, count in enumerate(h.histories):
                body += f"{count} "
                total += int(count)

            body += f"，總和 : {total}\n"

        embed.add_field(name="\u200b", value=body, inline=False)
        await ctx.response.send_message(embed=embed)
    except Exception as ex:
        print(ex, flush=True)
        await ctx.response.send_message(
            content="輸入錯誤，請檢查日期格式是否正確", ephemeral=True, delete_after=3
        )


@tree.command(
    name="broadcast_add",
    description="綁定廣播頻道（此指令只有管理員可以使用）",
    guild=discord.Object(id=guild_id),
)
@app_commands.describe(channel="要被廣播訊息的頻道")
@app_commands.rename(channel="頻道")
async def command_broadcast_add(ctx: discord.Interaction, channel: discord.TextChannel):
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


@tree.command(
    name="broadcast_rm",
    description="移除廣播頻道（此指令只有管理員可以使用）",
    guild=discord.Object(id=guild_id),
)
@app_commands.describe(channel="要被從清單中移除的頻道")
@app_commands.rename(channel="頻道")
async def command_broadcast_rm(ctx: discord.Interaction, channel: discord.TextChannel):
    try:
        if not perm.is_admin(ctx.user.id):
            await ctx.response.send_message(
                content="你沒有權限使用此指令", ephemeral=True
            )
            return

        broadcast.delete_channel(channel.guild.id, channel.id)
        await ctx.response.send_message(
            content=f"{channel.name} 已成功從廣播清單中移除", ephemeral=True
        )
    except Exception as ex:
        print(ex, flush=True)
        await ctx.response.send_message(content="發生錯誤", ephemeral=True)


@tree.command(
    name="broadcast_list",
    description="列出廣播頻道清單（此指令只有管理員可以使用）",
    guild=discord.Object(id=guild_id),
)
async def command_broadcast_list(ctx: discord.Interaction):
    try:
        if not perm.is_admin(ctx.user.id):
            await ctx.response.send_message(
                content="你沒有權限使用此指令", ephemeral=True
            )
            return

        channel_names = ""

        targets = broadcast.get_broadcast_targets()
        for target in targets:
            channel = client.get_guild(target["guildId"]).get_channel(
                target["channelId"]
            )
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


@tree.command(
    name="broadcast",
    description="向綁定的頻道廣播訊息（此指令只有管理員可以使用）",
    guild=discord.Object(id=guild_id),
)
@app_commands.describe(message="廣播的訊息內容")
@app_commands.rename(message="訊息內容")
async def command_broadcast(ctx: discord.Interaction, message: str):
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

        confirm_button = Button(
            style=discord.ButtonStyle.green,
            label="確認",
            custom_id="confirm",
        )
        confirm_button.callback = lambda i: confirm_broadcast(ctx, message)
        view.add_item(confirm_button)

        cancel_button = Button(
            style=discord.ButtonStyle.red,
            label="取消",
            custom_id="cancel",
        )
        cancel_button.callback = lambda i: cancel_broadcast(ctx)
        view.add_item(cancel_button)

        channel_names = ""
        for target in targets:
            channel = client.get_guild(target["guildId"]).get_channel(
                target["channelId"]
            )
            channel_names += channel.name + "\n"

        await ctx.response.send_message(
            content=f"即將發送廣播訊息：\n```\n{message}\n```\n給以下 **{len(targets)}** 個頻道：\n```{channel_names}```\n請確認是否繼續：",
            view=view,
            ephemeral=True,
        )

    except Exception as ex:
        print(ex, flush=True)
        await msg.reply_error(ctx, "發生未知錯誤")


async def confirm_broadcast(ctx: discord.Interaction, message: str):
    await ctx.delete_original_response()
    await broadcast.broadcast(client, message)


async def cancel_broadcast(ctx: discord.Interaction):
    await ctx.delete_original_response()


@tree.command(
    name="img",
    description="根據傳入的時間軸，產生隊伍角色的圖片。",
    guild=discord.Object(id=guild_id),
)
async def command_img(ctx: discord.Interaction):
    await ctx.response.send_modal(GenPicModal())


class GenPicModal(discord.ui.Modal, title="產生隊伍角色圖片"):
    timeline = discord.ui.TextInput(
        label="時間軸",
        placeholder="請輸入時間軸",
        required=True,
        style=discord.TextStyle.paragraph,
    )

    async def on_submit(self, interaction: discord.Interaction):
        tl = urllib.parse.quote(self.timeline.value)
        url = f"[隊伍圖片連結]({env.get_website_url()}?tl={tl})"
        await interaction.response.send_message(url, ephemeral=True)

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        await interaction.response.send_message(
            "發生錯誤，請聯繫管理員", ephemeral=True
        )

        print(error)


client.run(bot_token)
