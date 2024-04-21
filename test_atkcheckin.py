import asyncio
import unittest
import module.atkcheckin as atkcheckin
from module.msg import MessageWriter, MessageReader, TextMessage
from random import random


class FakeMessageReader(MessageReader):

    def __init__(self, messages: list[TextMessage] = []):
        self.messages = messages

    def push(self, message: TextMessage):
        self.messages.insert(0, message)

    async def read_all(self, limit: int) -> list[TextMessage]:
        return self.messages


class FakeMessageWriter(MessageWriter):
    def __init__(self, channel_id: int, reader: FakeMessageReader):
        self.reader = reader
        self.channel_id = channel_id
        self.messages = []

    async def write(self, content: str, mention: int = None, silent: bool = False):
        self.messages.append(f"<@{mention}> {content}")
        self.reader.push(TextMessage(content, random(), mention, self.channel_id))

    async def delete(self):
        pass


class GetRemainingHealthTest(unittest.TestCase):

    def test_1(self):
        self.assertEqual(
            atkcheckin.get_remaining_health("30000-5000=25000", 30000), 25000
        )
        self.assertEqual(
            atkcheckin.get_remaining_health("30000-8000=22000 等合", 30000), 22000
        )

    def test_2(self):
        self.assertEqual(atkcheckin.get_remaining_health("-25000", 30000), 30000)

    def test_3(self):
        self.assertEqual(atkcheckin.get_remaining_health("校正8500", 30000), 8500)
        self.assertEqual(atkcheckin.get_remaining_health("※13392", 30000), 13392)


# 模擬用的Discord機器人ID
BOT_ID = 965198519516521651

# 模擬用的呼叫者報刀訊息ID
COMMAND_ID = 216581981985145411

# 模擬用的Discord呼叫者ID
CALLER_ID = 516858946546521581

# 模擬用的Discord頻道ID
CHANNEL_ID = 698198198451846854

# 測試用的資料集合，包含多筆報刀歷史紀錄
MULTIPLE_HISTORIES = [
    TextMessage(
        content="<@351685198198165498> 22100-6300=15800",
        id=5,
        author_id=BOT_ID,
        channel_id=1,
    ),
    TextMessage(
        content="27600-5500=22100",
        id=4,
        author_id=654521848654385785,
        channel_id=1,
    ),
    TextMessage(
        content="無關的訊息",
        id=3,
        author_id=519851981981981981,
        channel_id=1,
    ),
    TextMessage(
        content="<@514189854651887762> 30000-2400=27600",
        id=2,
        author_id=BOT_ID,
        channel_id=1,
    ),
    TextMessage(
        content="<@987451523541884152> 32000-2000=30000",
        id=1,
        author_id=BOT_ID,
        channel_id=1,
    ),
]


def message_from_bot(content: str) -> TextMessage:
    return TextMessage(content, random(), BOT_ID, CHANNEL_ID)


def message_from_caller(content: str) -> TextMessage:
    return TextMessage(content, COMMAND_ID, CALLER_ID, CHANNEL_ID)


def command_option(command_lines: list[str]) -> atkcheckin.AttackCheckinOption:
    return atkcheckin.AttackCheckinOption(
        command_lines=command_lines,
        command_id=COMMAND_ID,
        caller_id=CALLER_ID,
        boss_id=CHANNEL_ID,
    )


class DoCommandTest(unittest.TestCase):

    def test_single_history(self):
        """
        測試報刀歷史紀錄僅有一筆的狀況
        """
        option = command_option(command_lines=["-5000"])
        reader = FakeMessageReader(
            messages=[
                message_from_caller(content="-5000"),
                message_from_bot(content="<@999> 32000-2000=30000"),
            ]
        )
        writer = FakeMessageWriter(channel_id=CHANNEL_ID, reader=reader)

        asyncio.run(atkcheckin.do_command(option, reader, writer))
        self.assertEqual(writer.messages, [f"<@{CALLER_ID}> 30000-5000=25000"])

    def test_multiple_histories(self):
        """
        測試報刀歷史紀錄有多筆的狀況
        """
        option = command_option(command_lines=["-3500"])
        reader = FakeMessageReader(
            messages=[
                message_from_caller(content="-3500"),
                *MULTIPLE_HISTORIES,
            ]
        )
        writer = FakeMessageWriter(channel_id=CHANNEL_ID, reader=reader)

        asyncio.run(atkcheckin.do_command(option, reader, writer))
        self.assertEqual(writer.messages, [f"<@{CALLER_ID}> 15800-3500=12300"])

    def test_multiple_damage(self):
        """
        測試報刀指令中有多個預估傷害的狀況
        """
        option = command_option(command_lines=["-3500-7000-5000-3400"])
        reader = FakeMessageReader(
            messages=[
                message_from_caller(content="-3500-7000-5000-3400"),
                *MULTIPLE_HISTORIES,
            ]
        )
        writer = FakeMessageWriter(channel_id=CHANNEL_ID, reader=reader)

        asyncio.run(atkcheckin.do_command(option, reader, writer))
        self.assertEqual(
            writer.messages, [f"<@{CALLER_ID}> 15800-3500-7000-5000-3400=-3100"]
        )

    def test_multiple_lines_command(self):
        """
        測試報刀指令有多行的狀況
        """
        option = command_option(
            command_lines=[
                "-2150",
                "-3498-4485",
                "-999",
            ]
        )
        reader = FakeMessageReader(
            messages=[
                message_from_caller(content="-999"),
                message_from_caller(content="-3498-4485"),
                message_from_caller(content="-2150"),
                *MULTIPLE_HISTORIES,
            ]
        )
        writer = FakeMessageWriter(channel_id=CHANNEL_ID, reader=reader)

        asyncio.run(atkcheckin.do_command(option, reader, writer))
        self.assertEqual(
            writer.messages,
            [
                f"<@{CALLER_ID}> 15800-2150=13650",
                f"<@{CALLER_ID}> 13650-3498-4485=5667",
                f"<@{CALLER_ID}> 5667-999=4668",
            ],
        )

    def test_damage_trailing_desc(self):
        """
        測試預估傷害後面有其他文字描述的狀況
        """
        option = command_option(
            command_lines=[
                "-2150這是訊息",
                "-3498這是第二訊息",
                "-999來合刀",
            ]
        )
        reader = FakeMessageReader(
            messages=[
                message_from_caller(content="-999來合刀"),
                message_from_caller(content="-3498這是第二訊息"),
                message_from_caller(content="-2150這是訊息"),
                *MULTIPLE_HISTORIES,
            ]
        )
        writer = FakeMessageWriter(channel_id=CHANNEL_ID, reader=reader)

        asyncio.run(atkcheckin.do_command(option, reader, writer))
        self.assertEqual(
            writer.messages,
            [
                f"<@{CALLER_ID}> 15800-2150=13650 這是訊息",
                f"<@{CALLER_ID}> 13650-3498=10152 這是第二訊息",
                f"<@{CALLER_ID}> 10152-999=9153 來合刀",
            ],
        )

    def test_damage_with_desc(self):
        """
        測試報刀指令中的預估傷害存在描述的狀況
        """
        option = command_option(
            command_lines=[
                "-補償2150",
                "-第一個補償3498-500-第二個補償4485",
                "-最後一個補償999",
            ]
        )
        reader = FakeMessageReader(
            messages=[
                message_from_caller(content="-最後一個補償999"),
                message_from_caller(content="-第一個補償3498-500-第二個補償4485"),
                message_from_caller(content="-補償2150"),
                *MULTIPLE_HISTORIES,
            ]
        )
        writer = FakeMessageWriter(channel_id=CHANNEL_ID, reader=reader)

        asyncio.run(atkcheckin.do_command(option, reader, writer))
        self.assertEqual(
            writer.messages,
            [
                f"<@{CALLER_ID}> 15800-補償2150=13650",
                f"<@{CALLER_ID}> 13650-第一個補償3498-500-第二個補償4485=5167",
                f"<@{CALLER_ID}> 5167-最後一個補償999=4168",
            ],
        )


if __name__ == "__main__":
    unittest.main()
