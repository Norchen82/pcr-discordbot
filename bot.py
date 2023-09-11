import os
import discord
from discord import app_commands
import module.cal as cal
import module.msg as msg

bot_token = os.getenv("BOT_TOKEN")
guild_id = os.getenv("GUILD_ID")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

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
    result = cal.compile(expr)
    message = f"{expr} = {result} {desc}".strip()
    await msg.reply_with_message(ctx, message)  

@tree.command(name="go", description="【報刀用指令】根據預估傷害計算BOSS的剩餘血量。", guild=discord.Object(id=guild_id))
@app_commands.describe(value="請輸入你本次出刀預估的傷害量。", desc="請輸入想在運算結果後面的附加訊息。例如:等合")
@app_commands.rename(value="預估傷害", desc="附加訊息")
async def command_go(ctx: discord.Interaction, value: str, desc: str = ""):
    """
    Retrieve the boss's remaining health points from the latest message in the channel,
    subtract the estimated damage points, and send the result to the user.
    """
    last_message = ctx.channel.last_message
    if last_message != None:
        tokens = last_message.content.split("校正")
        if len(tokens) <= 1:
            tokens = last_message.content.split("=")

        remaining = tokens[-1].strip()

        expr = f"{remaining} - {value}"
        result = cal.compile(expr)

        message = f"{expr} = {result} {desc}".strip()
        await msg.reply_with_message(ctx, message)  
        return
    
    await ctx.response.send_message("[錯誤] 無法自動偵測BOSS的剩餘血量，無法計算。(此訊息將在數秒後自動刪除)", ephemeral=True, delete_after=5)

@tree.command(name="fixh", description="【報刀用指令】校正BOSS的血量。", guild=discord.Object(id=guild_id))
@app_commands.describe(value="請輸入校正後的血量。")
@app_commands.rename(value="校正血量")
async def command_fixh(ctx: discord.Interaction, value: str):
    """
    Update the boss's health points with a fixed value.
    """
    result = int(value)
    message = f"校正{result}"
    await msg.reply_with_message(ctx, message)


client.run(bot_token)