import re
from discord import (
    ButtonStyle,
    SelectOption,
    Interaction,
    Message,
    TextChannel,
    User,
    Member,
)
from discord.ui import Select, Button, View
from module.msg import (
    is_round_divider,
    mention,
    reply_error,
    DiscordTextChannelWriter,
    DiscordTextChannelReader,
)
from module.atkcheckin import (
    do_command as do_atkcheckin,
    AttackCheckinOption,
    sub_estimated_damage,
)
import module.bot as bot

rm_queue: list[int] = []


class RmView(View):
    def __init__(self, caller: User | Member, messages: list[Message]):
        super().__init__()
        self.caller = caller
        self.messages = messages
        self.selected_id: str | None = None
        self.select: Select[RmView] | None = None
        self.delete_btn: Button[RmView] | None = None

        self.render_components()

    def render_components(self):
        self.render_select()
        self.render_delete_btn()

    def render_select(self):
        if self.select != None:
            self.remove_item(self.select)

        options: list[SelectOption] = []
        for message in self.messages:
            content: str = re.sub(mention(self.caller), "", message.content)
            value = str(message.id)
            is_default = value == self.selected_id
            options.append(SelectOption(label=content, value=value, default=is_default))

        self.select = Select(
            placeholder="請選擇要刪除的報刀紀錄",
            options=options,
            custom_id="rm_select",
        )
        if self.selected_id != None:
            self.select.values.append(self.selected_id)
        self.select.callback = self.on_select
        self.add_item(self.select)

    def render_delete_btn(self):
        if self.delete_btn != None:
            self.remove_item(self.delete_btn)

        if self.selected_id == None:
            return

        self.delete_btn = Button(
            style=ButtonStyle.danger,
            label="刪除",
            custom_id="rm_delete",
        )
        self.delete_btn.callback = self.on_delete
        self.add_item(self.delete_btn)

    async def on_select(self, interaction: Interaction):
        if self.select == None:
            return

        self.selected_id = self.select.values[0]
        self.render_components()

        await interaction.response.edit_message(view=self)

    async def on_delete(self, interaction: Interaction):
        if self.selected_id == None:
            return
        if interaction.channel == None or type(interaction.channel) is not TextChannel:
            return

        global rm_queue

        message_id = None
        try:
            message = await interaction.channel.fetch_message(int(self.selected_id))
            message_id = message.id

            content = message.content

            # 若該報刀紀錄已經被刪除，則不處理
            if message.content.startswith("~~") and message.content.endswith("~~"):
                await interaction.response.edit_message(
                    content="[錯誤] 報刀紀錄已經被刪除。", view=None, delete_after=5
                )
                return

            if rm_queue.count(message.id) > 0:
                await interaction.response.edit_message(
                    content="[錯誤] 報刀紀錄已經被刪除。", view=None, delete_after=5
                )
                return

            # 將訊息標記為待刪除
            rm_queue.append(message_id)

            # 擷取預估傷害的部分
            estimated_damage = sub_estimated_damage(content)

            # 將原本的預估傷害補回
            await do_atkcheckin(
                option=AttackCheckinOption(
                    command_lines=[estimated_damage],
                    command_id=message.id,
                    caller_id=interaction.user.id,
                    boss_id=interaction.channel.id,
                    reverse=True,
                ),
                reader=DiscordTextChannelReader(interaction.channel),
                writer=DiscordTextChannelWriter(interaction.channel),
            )

            # 將原報刀訊息標記為刪除
            await message.edit(content=f"~~{content}~~")

            # 將回應訊息刪除
            await interaction.response.edit_message(
                content="** **", view=None, delete_after=0
            )

            # 將訊息從待刪除清單中移除
            rm_queue.remove(message_id)
        except Exception as ex:
            print(ex)

            if message_id != None:
                rm_queue.remove(message_id)

            raise ex


async def do_command(interaction: Interaction):
    """
    處理刪除報刀的指令
    """
    if interaction.channel == None or type(interaction.channel) is not TextChannel:
        raise Exception("rm指令只允許在文字頻道中執行。")

    try:
        caller = interaction.user

        messages: list[Message] = []
        async for history in interaction.channel.history(limit=20):
            content = history.content

            # 遇到周次分隔線，停止動作
            if is_round_divider(content):
                break

            # 非機器人發送的訊息，不處理
            if history.author.id != bot.client_id():
                continue

            # 非本人的報刀訊息，不處理
            if not content.startswith(mention(caller)):
                continue

            # 字串中還有「取消報刀」的訊息，不處理
            if "取消報刀" in content:
                continue

            messages.append(history)

        # 沒有任何報刀紀錄
        if len(messages) == 0:
            await reply_error(interaction, f"本週次您尚未有透過機器人進行報刀的紀錄。")
            return

        # 因為訊息是由舊到新，所以要反轉
        messages.reverse()

        # send message with buttons
        await interaction.response.send_message(
            ephemeral=True,
            view=RmView(caller, messages),
        )
    except Exception as ex:
        print(ex)
        await interaction.response.send_message(content="發生錯誤", ephemeral=True)
        pass
