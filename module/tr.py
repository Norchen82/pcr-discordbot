COMMAND_PATTERN = ".tr "


class AdjustResult:
    def __init__(self, index: int, content: str):
        self.index = index
        self.content = content


class Time:
    def __init__(self, minutes: int, seconds: int):
        self.minutes = minutes
        self.seconds = seconds


def is_not_end(line: AdjustResult, end_line_index: int | None) -> bool:
    """判斷是否為有效的時間軸行"""
    return end_line_index is None or line.index <= end_line_index


def parse_time(time: str) -> int:
    """將輸入的時間文字轉換成秒數"""
    # 用分號來分隔
    tokens = time.split(":")

    parsed = 0

    # 若分號分隔出來有超過2個字段，或是沒有字段，表示格式有誤
    if len(tokens) > 2 or len(tokens) == 0:
        return int("nan")
    elif len(tokens) == 2:
        # 解析分與秒
        try:
            minutes = int(tokens[0])
            seconds = int(tokens[1])
        except ValueError:
            return int("nan")

        # 若為負數，表示格式不正確
        if minutes < 0 or seconds < 0:
            return int("nan")

        parsed = minutes * 60 + seconds
    elif len(tokens) == 1:
        try:
            seconds = int(tokens[0])
            # 如果輸入的是100以上的數字，將被視為1:00(也就是1分鐘)
            if seconds >= 100:
                parsed = seconds - 40
            else:
                parsed = seconds
        except ValueError:
            return int("nan")

    return parsed


def get_time(total_seconds: int) -> Time:
    """將輸入的總秒數轉成分秒格式的結構"""
    minutes = total_seconds // 60
    seconds = total_seconds - 60 * minutes
    return Time(minutes, seconds)


def format_time(time: Time, separator: str) -> str:
    """將輸入的分秒值轉換成時間文字"""
    m = str(time.minutes).zfill(1)
    ss = str(time.seconds).zfill(2)
    return f"{m}{separator}{ss}"


class TimelineAdjuster:
    """時間軸轉換模組"""

    def __init__(self):
        """初始化"""
        self.remaining_time = 0
        self.timeline = ""
        self.end_line_index = None

    def _to_adjusted(self, line: str, line_index: int) -> AdjustResult:
        """將一個時間軸的時間值根據時間差進行轉換"""
        # 計算跟1分30秒的時間差
        offset = 90 - self.remaining_time

        # 取得當前行的時間點
        import re

        matches = list(re.finditer(r"(\d{1,2}:\d{2}|\d{2,4})", line))
        if not matches:
            return AdjustResult(line_index, line)

        # 開始轉換所有時間
        pointer = 0
        result = ""

        for match in matches:
            if pointer != len(line):
                # 取得時間文字
                token = match.group(0)
                if not token:
                    continue

                # 取得索引位置
                index = match.start()

                # 如果數字後面接著'w' 或 '萬'，表示是當前的數字是在表示「傷害」而不是「時間」，故不做處理
                following = (
                    line[index + len(token)] if index + len(token) < len(line) else ""
                )
                if following in ["W", "w", "萬"]:
                    continue

                # 計算調整過後的時間 = 時間值 - 時間差
                total_seconds = parse_time(token) - offset

                if total_seconds >= 90:
                    result += line[pointer:index]  # 加入時間軸的操作文字
                    result += token  # 直接加入原始文字
                    pointer = index + len(token)  # 設定新的指針位置

                elif total_seconds >= 0:
                    time = get_time(total_seconds)  # 取得分秒結構
                    separator = (
                        ":" if ":" in token else ""
                    )  # 如果原始的時間軸文字包含分號，轉出來的時間格式就一樣保留分號

                    result += line[pointer:index]  # 加入時間軸的操作文字
                    result += format_time(time, separator)  # 加入轉換過的時間
                    pointer = index + len(token)  # 設定新的指針位置

                elif total_seconds < 0:
                    if pointer == 0:
                        # 如果一開始的時間就是負值，直接忽略整行
                        pointer = len(line)
                        if self.end_line_index is None:
                            self.end_line_index = line_index - 1
                    else:
                        result += line[pointer:index]  # 加入時間軸的操作文字
                        pointer = index + len(token)  # 設定新的指針位置

        result += line[pointer:]
        return AdjustResult(line_index, result)

    def set_remaining_time(self, time: str):
        """設定剩餘時間"""
        parsed_time = parse_time(time)
        if (
            parsed_time != parsed_time or parsed_time < 21 or parsed_time > 90
        ):  # parsed_time != parsed_time 用來檢查 NaN
            raise ValueError("RemainingTimeIsInvalid")

        self.remaining_time = parsed_time

    def set_timeline(self, timeline: str):
        """設定時間軸"""
        self.timeline = timeline

    def adjust(self) -> str:
        """根據剩餘時間調整時間軸的時間並回傳"""
        # 將時間軸按照換行分好
        lines = self.timeline.split("\n")

        # 調整前先重設指針
        self.end_line_index = None

        # 取得調整後的時間軸列表，並將每一行合併成一個整體文字後輸出
        adjusted_lines = [self._to_adjusted(line, i) for i, line in enumerate(lines)]
        valid_lines = [
            line for line in adjusted_lines if is_not_end(line, self.end_line_index)
        ]
        return "\n".join(line.content for line in valid_lines).strip()


def adjust_timeline(remaining_time: str, timeline: str) -> str:
    """調整時間軸"""
    adjuster = TimelineAdjuster()
    adjuster.set_remaining_time(remaining_time)
    adjuster.set_timeline(timeline)
    return adjuster.adjust()


class TrCommand:
    def __init__(self, remaining_time: str, timeline: str):
        self.remaining_time = remaining_time
        self.timeline = timeline


def parse_command(message: str) -> TrCommand | None:
    """
    解析時間軸調整指令。
    """
    if not message.startswith(COMMAND_PATTERN):
        return None

    # 移除指令開頭
    message = message[len(COMMAND_PATTERN) :]

    # 將剩餘秒數與時間軸分開
    parts = message.split("\n")

    if len(parts) < 2:
        return None

    remaining_time = parts[0]
    time_line = "\n".join(parts[1:])

    return TrCommand(remaining_time, time_line)
