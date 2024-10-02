import discord

from module.profile import (
    delete_subscription,
    get_profile,
    Subscription,
    add_subscription,
)
from module.pcrjjc import query_profile

create_action = "@create"

CREATE = "CREATE"
PLAYER_NOT_FOUND = "PLAYER_NOT_FOUND"
OK = "OK"


class SubscribeView(discord.ui.View):
    def __init__(
        self,
        user_id: int,
        player_id: str | None = None,
        user_data: dict[str, dict[str, str]] | None = None,
    ):
        super().__init__()
        self.user_id = user_id
        self.profile = get_profile(self.user_id)
        self.new_player_id = player_id
        self.user_data = user_data

        self.subscription: Subscription | None = None

        self.selected_id: str | None = None
        self.select: discord.ui.Select[SubscribeView] | None = None

        self.btn_arena: discord.ui.Button[SubscribeView] | None = None
        self.btn_grand_arena: discord.ui.Button[SubscribeView] | None = None
        self.btn_activity: discord.ui.Button[SubscribeView] | None = None

        self.btn_submit: discord.ui.Button[SubscribeView] | None = None

        if self.new_player_id is not None:
            if self.player_exists(self.new_player_id):
                self.selected_id = self.new_player_id
                self.subscription = self.subscription = next(
                    (
                        sub
                        for sub in self.subscriptions()
                        if sub.player_id == self.selected_id
                    ),
                    None,
                )
                self.new_player_id = None
                self.user_data = None
            else:
                self.selected_id = self.new_player_id
                self.subscription = self.new_player_subscription()

        self.render_components()

    def subscriptions(self) -> list[Subscription]:
        if self.profile is not None and self.profile.subscriptions is not None:
            return self.profile.subscriptions
        return []

    def state(self) -> str:
        if (
            self.new_player_id is not None
            and self.selected_id == self.new_player_id
            and self.user_data is None
        ):
            return PLAYER_NOT_FOUND

        if self.selected_id == create_action:
            return CREATE

        return OK

    def new_player_subscription(self) -> Subscription | None:
        if self.new_player_id is None:
            return None
        if self.user_data is None:
            return None

        return Subscription(
            type="player",
            player_id=self.new_player_id,
            player_name=self.user_data["user_info"]["user_name"],
            arena=False,
            grand_arena=False,
            activity=False,
        )

    def player_exists(self, player_id: str) -> bool:
        if self.profile is not None and self.profile.subscriptions is not None:
            return any(sub.player_id == player_id for sub in self.profile.subscriptions)
        return False

    def render_components(self):
        try:
            self.render_select()
            self.render_buttons()
            self.render_submit_button()
        except Exception as e:
            print(e)
            raise e

    def render_select(self):
        subscriptions = []
        if self.profile is not None and self.profile.subscriptions is not None:
            subscriptions = self.profile.subscriptions

        if self.select != None:
            self.remove_item(self.select)

        options = [map_select_option(subscription) for subscription in subscriptions]
        options.insert(
            0, discord.SelectOption(label="新增一個訂閱", value=create_action)
        )
        for option in options:
            option.default = option.value == self.selected_id

        if self.new_player_id is not None:
            player_name = (
                self.user_data["user_info"]["user_name"]
                if self.user_data is not None
                else "找不到玩家"
            )

            options.append(
                discord.SelectOption(
                    label=f"{self.new_player_id} - {player_name}",
                    value=self.new_player_id,
                    default=self.selected_id == self.new_player_id,
                )
            )

        self.select = discord.ui.Select(
            placeholder="請選擇訂閱項目",
            options=options,
            custom_id="ddl_subscription",
        )
        self.select.callback = self.on_select
        self.add_item(self.select)

    async def on_select(self, interaction: discord.Interaction):
        if self.select == None:
            return

        self.selected_id = self.select.values[0]
        if self.selected_id == self.new_player_id:
            self.subscription = self.new_player_subscription()
        elif self.profile is not None and self.profile.subscriptions is not None:
            self.subscription = next(
                (
                    sub
                    for sub in self.profile.subscriptions
                    if sub.player_id == self.selected_id
                ),
                None,
            )
        self.render_components()

        await interaction.response.edit_message(view=self)

    def render_buttons(self):
        if self.btn_arena != None:
            self.remove_item(self.btn_arena)
        if self.btn_grand_arena != None:
            self.remove_item(self.btn_grand_arena)
        if self.btn_activity != None:
            self.remove_item(self.btn_activity)

        if (
            self.state() == CREATE
            or self.state() == PLAYER_NOT_FOUND
            or self.subscription is None
        ):
            return

        style_1 = (
            discord.ButtonStyle.success
            if self.subscription.arena
            else discord.ButtonStyle.secondary
        )
        icon_1 = "🔔" if self.subscription.arena else "🔕"
        text_1 = "1v1 競技場通知"
        self.btn_arena = discord.ui.Button(
            style=style_1,
            label=f"{icon_1} {text_1}",
            custom_id="btn_arena",
        )
        self.btn_arena.callback = self.toggle_arena
        self.add_item(self.btn_arena)

        style_2 = (
            discord.ButtonStyle.success
            if self.subscription.grand_arena
            else discord.ButtonStyle.secondary
        )
        icon_2 = "🔔" if self.subscription.grand_arena else "🔕"
        text_2 = "3v3 競技場通知"
        self.btn_grand_arena = discord.ui.Button(
            style=style_2,
            label=f"{icon_2} {text_2}",
            custom_id="btn_grand_arena",
        )
        self.btn_grand_arena.callback = self.toggle_grand_arena
        self.add_item(self.btn_grand_arena)

        style_3 = (
            discord.ButtonStyle.success
            if self.subscription.activity
            else discord.ButtonStyle.secondary
        )
        icon_3 = "🔔" if self.subscription.activity else "🔕"
        text_3 = "玩家登入通知"
        self.btn_activity = discord.ui.Button(
            style=style_3,
            label=f"{icon_3} {text_3}",
            custom_id="btn_activity",
        )
        self.btn_activity.callback = self.toggle_activity
        self.add_item(self.btn_activity)

    async def toggle_arena(self, interaction: discord.Interaction):
        if self.subscription == None:
            return

        self.subscription.arena = not self.subscription.arena
        self.render_components()
        await interaction.response.edit_message(view=self)

    async def toggle_grand_arena(self, interaction: discord.Interaction):
        if self.subscription == None:
            return

        self.subscription.grand_arena = not self.subscription.grand_arena
        self.render_components()
        await interaction.response.edit_message(view=self)

    async def toggle_activity(self, interaction: discord.Interaction):
        if self.subscription == None:
            return

        self.subscription.activity = not self.subscription.activity
        self.render_components()
        await interaction.response.edit_message(view=self)

    def render_submit_button(self):
        if self.btn_submit is not None:
            self.remove_item(self.btn_submit)

        if self.selected_id is None:
            return

        if self.state() == PLAYER_NOT_FOUND:
            self.btn_submit = discord.ui.Button(
                style=discord.ButtonStyle.primary,
                label="✏️ 重新輸入",
                custom_id="btn_submit",
            )
        else:
            self.btn_submit = discord.ui.Button(
                style=discord.ButtonStyle.primary,
                label="✅ 確認",
                custom_id="btn_submit",
            )
        self.btn_submit.callback = self.on_submit
        self.add_item(self.btn_submit)

    async def on_submit(self, interaction: discord.Interaction):
        if self.state() == CREATE or self.state() == PLAYER_NOT_FOUND:
            await interaction.response.send_modal(SubscribeModal())
            return
        if self.subscription is None:
            return

        if (
            self.subscription.arena
            or self.subscription.grand_arena
            or self.subscription.activity
        ):
            add_subscription(self.user_id, self.subscription)
        else:
            delete_subscription(self.user_id, self.subscription)

        await interaction.response.edit_message(
            content=self.result_message(self.subscription), view=None
        )

    def result_message(self, subscription: Subscription) -> str:
        if (
            not subscription.arena
            and not subscription.grand_arena
            and not subscription.activity
        ):
            return f"已成功儲存，您將不會再收到任何來自玩家**{subscription.player_name}**的通知。"

        message = "已成功儲存，您將會在以下情況收到通知：\n\n"
        if subscription.arena:
            message += (
                f"玩家**{subscription.player_name}**在１v１競技場的名次降低時。\n"
            )

        if subscription.grand_arena:
            message += (
                f"玩家**{subscription.player_name}**在３v３競技場的名次降低時。\n"
            )

        if subscription.activity:
            message += f"玩家**{subscription.player_name}**登入遊戲時。\n"

        return message


class SubscribeModal(discord.ui.Modal, title="新增訂閱"):
    text = discord.ui.TextInput[discord.ui.Modal](
        label="玩家 ID",
        placeholder="請輸入玩家 ID",
        required=True,
        min_length=10,
        max_length=10,
    )

    async def on_submit(self, interaction: discord.Interaction):
        res = None
        if check_player_id(self.text.value):
            try:
                res = await query_profile(self.text.value)
                if "user_info" not in res:
                    res = None
            except Exception as e:
                print(e)

        await interaction.response.edit_message(
            view=SubscribeView(interaction.user.id, self.text.value, res),
        )


async def do_command(interaction: discord.Interaction):
    await interaction.response.send_message(
        ephemeral=True,
        view=SubscribeView(interaction.user.id),
    )


def map_select_option(subscription: Subscription):
    return discord.SelectOption(
        label=f"{subscription.player_id} - {subscription.player_name}",
        value=subscription.player_id,
    )


def check_player_id(player_id: str):
    # must be 10 digits number
    return player_id.isdigit() and len(player_id) == 10
