import os
import discord
from discord import app_commands
import module.cal as cal
import module.msg as msg
import module.types as types
import re

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
    try:
        result = cal.compile(expr)
        message = f"{expr}={result} {desc}".strip()
        await msg.reply_with_message(ctx, message) 
    except:
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
        last_message = ctx.channel.last_message
        if last_message != None:
            # Separate boss remaining health from the lastest message.
            pattern = r"\=|(校正(為)?(：|:)?)|(剩(下)?)"
            parts = re.split(pattern, last_message.content)
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
    except:
        await msg.reply_error(ctx, f"無法自動偵測BOSS的剩餘血量，請使用**/cal**指令來計算血量。")

client.run(bot_token)