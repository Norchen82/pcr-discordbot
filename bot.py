import os
import discord
from discord import app_commands
import module.cal as cal
import module.msg as msg
import re
from datetime import datetime, timedelta
import pytz

bot_token = os.getenv("BOT_TOKEN")
guild_id = os.getenv("GUILD_ID")


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

guild = client.get_guild(int(guild_id))

# Bind the health to the boss channel
boss_health = {}
for index in range(0,6):
    key = os.getenv(f"BOSS{index}_CHANNEL")
    if key == None or key == "":
        continue

    channel_ids = key.split(",")
    for id in channel_ids:
        boss_health[int(id)] = int(os.getenv(f"BOSS{index}_HEALTH"))

boss_title = {
    1: "一王",
    2: "二王",
    3: "三王",
    4: "四王",
    5: "五王",
}

master_id = int(os.getenv("MASTER_ID"))

role_ids = os.getenv("ROLE_ID").split(",")
role_names = os.getenv("ROLE_NAME").split(",")
role_choices = []
for index, role_id in enumerate(role_ids):
    role_choices.append(app_commands.Choice(name=role_names[index], value=role_ids[index]))

class History:
    def __init__(self, member_id: int, histories: list):
        self.member_id = member_id
        self.histories = histories

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=guild_id))
    print(f"Logged on as {client.user}")


@tree.command(name="cal", description="簡易計算機，支援四則運算", guild=discord.Object(id=guild_id))
@app_commands.describe(
    expr="請輸入數學算式，不要包含等號。例如:24000-4800", desc="請輸入想在運算結果後面的附加訊息。例如:等合"
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
        await ctx.response.send_message(f'"{expr}"不是一個有效的運算式。', ephemeral=True, delete_after=5)


@tree.command(name="go", description="【報刀用指令】根據預估傷害計算BOSS的剩餘血量。", guild=discord.Object(id=guild_id))
@app_commands.describe(value="請輸入你本次出刀預估的傷害量。", desc="請輸入想在運算結果後面的附加訊息。例如:等合")
@app_commands.rename(value="預估傷害", desc="附加訊息")
async def command_go(ctx: discord.Interaction, value: str, desc: str = ""):
    """
    Retrieve the boss remaining health points from the latest message in the channel,
    subtract the estimated damage points, and send the result to the user.
    """
    try:
        last_message = await msg.last_message(ctx)
        if last_message != None:
            content = last_message.content
            remaining_health = 0
            if msg.is_round_divider(content):
                remaining_health = boss_health[ctx.channel.id]
            else:
                # Separate boss remaining health from the lastest message.
                pattern = r"\=|(校正(為)?(：|:)?)|(剩(下)?)|※"
                parts = re.split(pattern, content)
                remaining_health = cal.compile(parts[-1].strip())
                if remaining_health <= 0:
                    await msg.reply_error(ctx, f'偵測到BOSS血量低於0，請透過**/cal**指令重新計算血量。')
                    return
        
            # If the estimated damage does not start with minus symbol, insert one at the beginning.
            estimated_damage = value.strip()
            if not estimated_damage.startswith("-"):
                estimated_damage = "-" + estimated_damage

            # Calculate result of `Boss remaining health` - `Estimated damage`.
            expr = f"{remaining_health}{estimated_damage}"
            result = cal.compile(expr)

            message = f"{expr}={result} {desc}".strip()
            await msg.reply_with_message(ctx, message)  
            return
        
        raise Exception("Cannot fetch last message")
    except Exception as ex:
        print(f"value={value}, desc={desc}, ex={ex}")
        await msg.reply_error(ctx, f"無法自動偵測BOSS的剩餘血量，請使用**/cal**指令來計算血量。")

@tree.command(name="rm", description="【報刀用指令】刪除你本週次出的最後一個刀。", guild=discord.Object(id=guild_id))
async def command_rm(ctx: discord.Interaction):
    try:
        last_attack = None
       
        async for history in ctx.channel.history(limit=10):
            content = history.content
            if msg.is_round_divider(content): # Reach the beginning of the current round, stop iterating.
                break
            elif content.startswith(msg.mention(ctx.user)) and history.author.id == client.user.id: # Found the last attack of the current user, stop iterating.
                last_attack = history
                break
            
        # The current user haven't make any attack yet.
        if last_attack == None:
            await msg.reply_error(ctx, f"本週次您尚未出刀。")
            return

        # Send an empty message and delete it instantly, so the user won't see any message
        await ctx.response.send_message(content="** **", ephemeral=True, delete_after=0)

        await last_attack.delete()
    except Exception as ex:
        print(f"rm: error with {ex}")
        pass

@tree.command(name="history", description="查看指定日期各戰隊成員在報刀區的總留言數。（警告：此功能測試中，不保證運作正確）", guild=discord.Object(id=guild_id))
@app_commands.describe(role="要查詢的戰隊",datestr="要查詢的日期，格式:yyyy-mm-dd")
@app_commands.rename(role="戰隊",datestr="日期")
@app_commands.choices(role=role_choices)
async def command_history(ctx: discord.Interaction, role: app_commands.Choice[str], datestr: str):
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
            histories[member.id] = [0,0,0,0,0]

        histories[master_id] = [0,0,0,0,0]

        for index in range(1, 6):
            channel_ids = os.getenv(f"BOSS{index}_CHANNEL").split(",")
            role_index = role_ids.index(role.value)
          
            channel = ctx.guild.get_channel(int(channel_ids[role_index]))
            h = [history async for history in channel.history(after=begin_time, before=end_time)]
            for history in h:
                member_id = history.author.id
                if member_id == client.user.id:
                    matches = re.findall(r"<@\d+>", history.content)
                    match = str(matches[0])

                    member_id = int(match[2:-1])

                histories[member_id][index-1] += 1
     
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

        # await ctx.response.send_message(embed=embed, ephemeral=True)
        await ctx.response.send_message(embed=embed)
    except Exception as ex:
        print(ex, flush=True)
        await ctx.response.send_message(content="輸入錯誤，請檢查日期格式是否正確", ephemeral=True, delete_after=3)
        
client.run(bot_token)

