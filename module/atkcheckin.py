import asyncio
import re
import module.msg as msg
import module.env as env
import module.cal as cal
from typing import List

COMMAND_PATTERN = r"^(\-[^\-\=\d]*\d+)"
DAMAGE_PATTERN = r"(\-[^\-\=\d]*\d+(\s*[xX\*]\s*\d+)?(\s*\(?補償?刀?\)?)?)"
DAMAGE_PATTERN_FOR_SPLIT = (
    r"(?:\-[^\-\=\d]*\d+(?:\s*[xX\*]\s*\d+)?(?:\s*\(?補償?刀?\)?)?)"
)
PURE_DAMAGE_PATTERN = r"[^xX\*\-\d]"

checkin_queue = {}


def parse_remaining_health(lines: List[str], max_health: int):
    """
    從周次報刀訊息中取得剩餘血量。
    """
    remaining_health = max_health

    for line in lines:
        remaining_health = get_remaining_health(line, remaining_health)

    return remaining_health


def get_remaining_health(line: str, current_health: int) -> int:
    try:
        line = line.strip()

        # 如果有包含"<@數字>"的格式，就先把它去掉
        line = re.sub(r"<@\d+>", "", line)
        line = line.strip()

        # 判斷字串是否符合 -數字 的格式，如果符合直接忽略
        if re.match(r"^(\-\d+)+$", line):
            return current_health

        # 如果中間有貼圖，就先把貼圖移除
        line = re.sub(r"<:.+:\d+>", "", line)

        # 抓等號後的數字做為剩餘血量
        damage = re.findall(r"\=\d+", line)
        if len(damage) > 0:
            return int(damage[-1].strip().replace("=", ""))

        # 除此之外，直接使用該訊息行中，所包含的最後一個數字數值(含負數)當作剩餘血量
        parts = re.findall(r"\-?\d+", line)
        return int(parts[-1].strip())
    except:
        return current_health


def is_command(lines: list[str]) -> bool:
    """
    判斷當前的訊息是否為報刀指令。
    """
    for line in lines:
        if re.match(COMMAND_PATTERN, line):
            return True
    return False


def push_checkin_queue(boss_id: int, unique_id: str):
    """
    將報刀訊息加入報刀佇列。
    """
    if boss_id not in checkin_queue:
        checkin_queue[boss_id] = []

    checkin_queue[boss_id].append(unique_id)


def pop_checkin_queue(group_id: int):
    """
    將報刀佇列中的第一個報刀訊息移除。
    """
    if group_id not in checkin_queue:
        return

    checkin_queue[group_id].pop(0)


def get_checkin_queue(group_id: int):
    """
    取得報刀佇列。
    """
    if group_id not in checkin_queue:
        return []

    return checkin_queue[group_id]


def is_current_checkin(unique_id: str, group_id: int) -> bool:
    """
    判斷報刀訊息是否為當前報刀
    """
    if group_id not in checkin_queue:
        return False

    if len(checkin_queue[group_id]) == 0:
        return False

    return checkin_queue[group_id][0] == unique_id


def sub_estimated_damage(line: str) -> str:
    """
    從報刀訊息中擷取預估傷害的部分
    """
    line = line.split("=")[0]

    # 如果有包含"<@數字>"的格式，就先把它去掉
    line = re.sub(r"<@\d+>", "", line).strip()

    if line.startswith("-"):
        line = line[1:]

    # 從報刀訊息中取得所有的預估傷害
    damage_strings = re.findall(DAMAGE_PATTERN, line)
    damage_strings = [re.sub(r"\s", "", damage[0].strip()) for damage in damage_strings]

    # 將所有的預估傷害轉換成純數字格式
    pure_damages = [
        re.sub(PURE_DAMAGE_PATTERN, "", damage) for damage in damage_strings
    ]

    return "".join(pure_damages)


class AttackCheckinOption:
    def __init__(
        self,
        command_lines: list[str],
        command_id: int,
        caller_id: int,
        boss_id: int,
        reverse: bool = False,
    ):
        self.command_lines = command_lines
        self.command_id = command_id
        self.caller_id = caller_id
        self.boss_id = boss_id
        self.reverse = reverse


async def do_command(
    option: AttackCheckinOption, reader: msg.MessageReader, writer: msg.MessageWriter
):
    command_lines = option.command_lines
    command_id = option.command_id
    caller_id = option.caller_id
    boss_id = option.boss_id

    # 已發送的非報刀的訊息
    not_attack_messages = []

    for index, line in enumerate(command_lines):
        # 如果非報刀訊息，就不處理
        if not re.match(COMMAND_PATTERN, line):
            # 如果不是周次分隔符號，就直接回覆原始訊息
            if not msg.is_round_divider(line):
                not_attack_messages.append(
                    await writer.write(content=line, mention=caller_id, silent=True)
                )
            else:
                not_attack_messages.append(
                    await writer.write(content=line, silent=True)
                )
            continue

        # 先將此報刀訊息加入報刀佇列
        if not option.reverse:
            queue_key = f"{command_id}_{index}"
            push_checkin_queue(boss_id, queue_key)

        # 前期定義
        deleting = False

        try:
            # 如果佇列中的報刀訊息不是當前的訊息，就等待
            if not option.reverse:
                while not is_current_checkin(queue_key, boss_id):
                    await asyncio.sleep(0.25)

            # 從報刀訊息中取得所有的預估傷害
            damage_strings = re.findall(DAMAGE_PATTERN, line)
            damage_strings = [
                re.sub(r"\s", "", damage[0].strip()) for damage in damage_strings
            ]

            # 將所有的預估傷害轉換成純數字格式
            pure_damages = [
                re.sub(PURE_DAMAGE_PATTERN, "", damage.strip())
                for damage in damage_strings
            ]

            # 處理過往訊息
            estimated_damage = "".join(pure_damages)
            if option.reverse:
                estimated_damage = re.sub(r"\-", "+", estimated_damage)

            max_health = env.get_boss_health(boss_id)
            lines = await msg.get_round_lines(reader, get_checkin_queue(boss_id))
            if lines == None:
                raise Exception("No round lines found.")

            remaining_health = parse_remaining_health(lines, max_health)

            # 計算運算式 `首領剩餘血量` - `預估傷害`.
            expr = f"{remaining_health}{estimated_damage}"
            result = cal.compile(expr)

            # 將報刀訊息中的運算式和描述分開
            tokens = re.split(DAMAGE_PATTERN_FOR_SPLIT, line)
            tokens = [
                token for token in tokens if token != None and token.strip() != ""
            ]

            desc = " ".join(
                [token for token in tokens if token != None and token.strip() != ""]
            ).strip()
            # 如果描述剛好為"="，就不顯示
            if desc == "=":
                desc = ""

            # 回覆報刀訊息
            middle = "".join(damage_strings)
            reply_message = f"{remaining_health}{middle}={result} {desc}".strip()
            if option.reverse:
                reply_message = f"取消報刀：{remaining_health}{estimated_damage}={result} {desc}".strip()

            await writer.write(content=reply_message, mention=caller_id, silent=True)

            # 如果是取消報刀，則不會有原始報刀訊息，故停止後續動作
            if option.reverse:
                return

            # 將這個報刀訊息從佇列中移除
            if is_current_checkin(queue_key, boss_id):
                pop_checkin_queue(boss_id)

            # 刪除當前這個報刀訊息
            if index == len(command_lines) - 1:
                deleting = True
                await writer.delete()

        except Exception as ex:
            print(ex)

            if deleting:
                # 如果在刪除訊息時發生錯誤，就把所有已發送的非報刀訊息刪除
                if len(not_attack_messages) > 0:
                    for message in not_attack_messages:
                        await writer.delete_by_id(message.id)

            if option.reverse:
                raise ex

            if is_current_checkin(queue_key, boss_id):
                pop_checkin_queue(boss_id)
            raise ex
