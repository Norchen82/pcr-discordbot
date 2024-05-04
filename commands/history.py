from datetime import datetime, timedelta
import discord
from discord import app_commands
import pytz
from module import cfg, bot
import os
import re
import bot


class History:
    def __init__(self, member_id: int, histories: list[int]):
        self.member_id = member_id
        self.histories = histories


async def do_command(
    ctx: discord.Interaction, role: app_commands.Choice[str], datestr: str
):
    try:
        if ctx.guild is None:
            raise Exception("The guild is not found.")

        # 檢查伺服器管理員ID是否正確
        master_id = cfg.master_id()
        if master_id == None:
            raise Exception("The master ID is not found.")

        timezone_tw = pytz.timezone("ROC")
        date = datetime.strptime(datestr, "%Y-%m-%d").replace(tzinfo=timezone_tw)

        # Day refresh on 05:00 a.m. everyday
        begin_time = date + timedelta(hours=5)
        end_time = begin_time + timedelta(days=1)

        # Initialize member map
        drole = ctx.guild.get_role(int(role.value))
        if drole is None:
            raise Exception("The role is not found.")

        histories: dict[int, list[int]] = {}
        for member in drole.members:
            histories[member.id] = [0, 0, 0, 0, 0]

        histories[master_id] = [0, 0, 0, 0, 0]

        # FIXME: 應改為直接loop戰隊資料
        for index in range(1, 6):
            channel_ids = str(os.getenv(f"BOSS{index}_CHANNEL")).split(",")
            clans = cfg.clans()
            role_index = next(
                (i for i, clan in enumerate(clans) if clan.role_id == int(role.value)),
                None,
            )

            if role_index == None:
                raise Exception("The role is not found.")

            channel = ctx.guild.get_channel(int(channel_ids[role_index]))
            if not isinstance(channel, discord.TextChannel):
                raise Exception("The channel is not found.")

            h = [
                history
                async for history in channel.history(after=begin_time, before=end_time)
            ]
            for history in h:
                member_id = history.author.id
                if member_id == bot.client_id():
                    matches = re.findall(r"<@\d+>", history.content)
                    match = str(matches[0])

                    member_id = int(match[2:-1])

                histories[member_id][index - 1] += 1

        hl: list[History] = []
        for key in histories:
            hl.append(History(member_id=key, histories=histories[key]))
        hl = sorted(hl, key=lambda x: sum(x.histories), reverse=True)

        embed = discord.Embed(title=f"{datestr} {role.name}成員出刀紀錄")
        body = ""
        for h in hl:
            member = ctx.guild.get_member(h.member_id)
            if member is None:
                raise Exception("The member is not found.")

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
