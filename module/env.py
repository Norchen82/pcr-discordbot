# Bind the health to the boss channel
import os
from discord import Client


class Role:
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name

    def __str__(self):
        return self.name


boss_healths = {}
master_id = None
dev_id = None
roles: list[Role] = []
website_url = None
client: Client | None = None


def init(c: Client):
    """
    初始化環境變數
    """
    global client
    client = c

    init_masters()
    init_roles()
    init_boss_healths()
    init_website_url()


def init_masters():
    """
    初始化Discord頻道管理員的使用者ID
    """
    global master_id
    env_value = os.getenv("MASTER_ID")
    if env_value != None and env_value != "":
        master_id = int(env_value)
    print("Master ID is loaded.")

    global dev_id
    env_value = os.getenv("DEV_ID")
    if env_value != None and env_value != "":
        dev_id = int(env_value)
    print("Dev ID is loaded.")


def init_roles():
    """
    初始化Discord頻道中與戰隊戰相關的身分組
    """
    global roles
    id_value = os.getenv("ROLE_ID")
    if id_value != None and id_value != "":
        role_ids = id_value.split(",")
        role_names = os.getenv("ROLE_NAME").split(",")

        for index in range(0, len(role_ids)):
            roles.append(Role(role_ids[index], role_names[index]))
    print("Roles are loaded.")


def init_boss_healths():
    """
    初始化所有首領的滿血血量
    """
    global boss_healths

    for index in range(0, 6):
        key = os.getenv(f"BOSS{index}_CHANNEL")
        if key == None or key == "":
            continue

        channel_ids = key.split(",")
        for id in channel_ids:
            boss_healths[int(id)] = int(os.getenv(f"BOSS{index}_HEALTH"))
    print("Boss healths are loaded.")


def init_website_url():
    """
    初始化網站的URL
    """
    global website_url
    env_value = os.getenv("WEBSITE_URL")
    if env_value != None and env_value != "":
        website_url = env_value
    print("Website URL is loaded.")


def get_boss_health(boss_id: int) -> int | None:
    """
    取得指定的首領的滿血血量
    """
    if boss_id not in boss_healths:
        return None

    return boss_healths[boss_id]


def get_master_id() -> int | None:
    """
    取得Discord頻道管理員的使用者ID
    """
    return master_id


def get_dev_id() -> int | None:
    """
    取得機器人開發者的使用者ID
    """
    return dev_id


def get_roles() -> list[Role]:
    """
    取得Discord頻道中與戰隊戰相關的身分組清單
    """
    return roles


def get_website_url() -> str | None:
    """
    取得戰隊戰作業製圖網站的URL
    """
    return website_url


def bot_client() -> Client:
    """
    取得機器人的客戶端實體
    """
    return client


def bot_client_id() -> int:
    """
    取得機器人的使用者ID
    """
    return client.user.id
