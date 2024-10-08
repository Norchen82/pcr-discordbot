# Bind the health to the boss channel
import json
import os

root_dir: str = ""


class ChannelConfig:
    def __init__(self, id: int, health: int):
        self.id = id
        self.health = health


class ClanConfig:
    def __init__(
        self,
        role_id: int,
        role_name: str,
        boss_channels: list[ChannelConfig] = [],
    ):
        self.role_id = role_id
        self.role_name = role_name
        self.boss_channels = boss_channels


class MongoDbConfig:
    def __init__(
        self,
        protocol: str = "mongodb",
        host: str | None = None,
        user: str | None = None,
        password: str | None = None,
        port: int = 27017,
    ):
        self.protocol = protocol
        self.host = host
        self.user = user
        self.password = password
        self.port = port


class Role:
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name

    def __str__(self):
        return self.name


class ClanBattleNotificationConfigClan:
    def __init__(
        self,
        leader_viewer_id: int,
        guild_id: int,
        channel_id: int | None = None,
        thread_id: int | None = None,
        cron: str | None = None,
        polling_channel_id: int | None = None,
        polling_channel_name: str | None = None,
        update_on_start: bool = False,
    ):
        self.leader_viewer_id = leader_viewer_id
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.thread_id = thread_id
        self.cron = cron
        self.polling_channel_id = polling_channel_id
        self.polling_channel_name = polling_channel_name
        self.update_on_start = update_on_start


class ClanBattleNotificationConfig:
    def __init__(
        self,
        clans: list[ClanBattleNotificationConfigClan] = [],
    ):
        self.clans = clans


class BotConfiguration:
    def __init__(
        self,
        bot_token: str = "",
        guild_id: int = 0,
        master_id: int | None = None,
        dev_id: int | None = None,
        clans: list[ClanConfig] = [],
        website_url: str | None = None,
        mongo: MongoDbConfig | None = None,
        clan_battle_notification: ClanBattleNotificationConfig | None = None,
        bot_clan_id: int | None = None,
    ):
        self.bot_token = bot_token
        self.guild_id = guild_id
        self.master_id = master_id
        self.dev_id = dev_id
        self.clans: list[ClanConfig] = clans
        self.website_url = website_url
        self.mongo = mongo
        self.clan_battle_notification = clan_battle_notification
        self.bot_clan_id = bot_clan_id


class JsonConfigLoader:
    __JSON_CONFIG: str = "config.json"

    def __init__(self, env: BotConfiguration):
        self.__env = env

    def load(self):
        with open(self.__JSON_CONFIG, "r", encoding="utf-8") as file:
            data = json.load(file)

            if "botToken" not in data:
                raise ValueError("The 'botToken' field is required.")
            self.__env.bot_token = data["botToken"]

            if "guildId" not in data:
                raise ValueError("The 'guildId' field is required.")
            self.__env.guild_id = data["guildId"]

            if "masterId" in data:
                self.__env.master_id = data["masterId"]

            if "devId" in data:
                self.__env.dev_id = data["devId"]

            # 載入戰隊設定
            if "clans" in data:
                for clan in data["clans"]:
                    if "roleId" not in clan:
                        raise ValueError("The 'roleId' field is required in 'clans'.")

                    role_id = clan["roleId"]

                    if "roleName" not in clan:
                        raise ValueError("The 'roleName' field is required in 'clans'.")

                    role_name = clan["roleName"]

                    boss_channels: list[ChannelConfig] = []
                    if "bossChannels" in clan:
                        for channel in clan["bossChannels"]:
                            if "id" not in channel:
                                raise ValueError(
                                    "The 'id' field is required in 'bossChannels'."
                                )
                            if "health" not in channel:
                                raise ValueError(
                                    "The 'health' field is required in 'bossChannels'."
                                )

                            boss_channels.append(
                                ChannelConfig(channel["id"], channel["health"])
                            )

                    self.__env.clans.append(
                        ClanConfig(role_id, role_name, boss_channels)
                    )

            if "websiteUrl" in data:
                self.__env.website_url = data["websiteUrl"]

            if "mongo" in data:
                mongo = MongoDbConfig()

                if "host" not in data["mongo"]:
                    raise ValueError("The 'mongo.host' field is required.")
                mongo.host = data["mongo"]["host"]

                if "user" not in data["mongo"]:
                    raise ValueError("The 'mongo.user' field is required.")
                mongo.user = data["mongo"]["user"]

                if "password" not in data["mongo"]:
                    raise ValueError("The 'mongo.password' field is required.")
                mongo.password = data["mongo"]["password"]

                if "port" in data["mongo"]:
                    mongo.port = data["mongo"]["port"]

                if "protocol" in data["mongo"]:
                    mongo.protocol = data["mongo"]["protocol"]

                self.__env.mongo = mongo

            if "clanBattleNotification" in data:
                if "clans" in data["clanBattleNotification"]:
                    clans: list[ClanBattleNotificationConfigClan] = []
                    for clan in data["clanBattleNotification"]["clans"]:
                        if "leaderViewerId" not in clan:
                            raise ValueError(
                                "The 'leaderViewerId' field is required in 'clanBattleNotification.clans'."
                            )

                        leader_viewer_id = clan["leaderViewerId"]
                        if "guildId" not in clan:
                            raise ValueError(
                                "The 'guildId' field is required in 'clanBattleNotification.clans'."
                            )

                        guild_id = clan["guildId"]

                        channel_id = (
                            int(clan["channelId"]) if "channelId" in clan else None
                        )
                        thread_id = (
                            int(clan["threadId"]) if "threadId" in clan else None
                        )
                        cron = clan["cron"] if "cron" in clan else None
                        polling_channel_id = (
                            int(clan["pollingChannelId"])
                            if "pollingChannelId" in clan
                            else None
                        )
                        polling_channel_name = (
                            clan["pollingChannelName"]
                            if "pollingChannelName" in clan
                            else None
                        )
                        update_on_start = (
                            clan["updateOnStart"] if "updateOnStart" in clan else False
                        )

                        clans.append(
                            ClanBattleNotificationConfigClan(
                                leader_viewer_id,
                                guild_id,
                                channel_id,
                                thread_id,
                                cron,
                                polling_channel_id,
                                polling_channel_name,
                                update_on_start,
                            )
                        )

                    self.__env.clan_battle_notification = ClanBattleNotificationConfig(
                        clans
                    )

            if "botClanId" in data:
                self.__env.bot_clan_id = data["botClanId"]

    @classmethod
    def config_file_name(cls) -> str:
        return cls.__JSON_CONFIG


class EnvironmentVariableLoader:
    def __init__(self, env: BotConfiguration):
        self.__env = env

    def load(self):
        self.__load_masters()
        self.__load_clans()
        self.__load_mongo()
        self.__load_website_url()

    def __load_masters(self):
        env_value = os.getenv("MASTER_ID")
        if env_value != None and env_value != "":
            self.__env.master_id = int(env_value)

        env_value = os.getenv("DEV_ID")
        if env_value != None and env_value != "":
            self.__env.dev_id = int(env_value)

    def __load_clans(self):
        clans: list[ClanConfig] = []

        env_role_id = os.getenv("ROLE_ID")
        if env_role_id == None or env_role_id == "":
            raise ValueError("The 'ROLE_ID' environment variable is required.")

        env_role_name = os.getenv("ROLE_NAME")
        if env_role_name == None or env_role_name == "":
            raise ValueError("The 'ROLE_NAME' environment variable is required.")

        role_ids = env_role_id.split(",")
        role_names = env_role_name.split(",")

        for index in range(0, len(role_ids)):
            clans.append(ClanConfig(int(role_ids[index]), role_names[index]))

        for index in range(0, 6):
            key = os.getenv(f"BOSS{index}_CHANNEL")
            if key == None or key == "":
                continue

            channel_ids = key.split(",")
            for index, channel_id in enumerate(channel_ids):
                env_boss_health = os.getenv(f"BOSS{index}_HEALTH")
                if env_boss_health == None or env_boss_health == "":
                    raise ValueError(
                        f"The 'BOSS{index}_HEALTH' environment variable is required."
                    )

                clans[index].boss_channels.append(
                    ChannelConfig(int(channel_id), int(env_boss_health))
                )
        self.__env.clans = clans

    def __load_mongo(self):
        self.__env.mongo = MongoDbConfig()

        env_value = os.getenv("MONGO_INITDB_ROOT_USERNAME")
        if env_value != None and env_value != "":
            self.__env.mongo.user = env_value

        env_value = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
        if env_value != None and env_value != "":
            self.__env.mongo.password = env_value

        env_value = os.getenv("MONGO_HOST")
        if env_value != None and env_value != "":
            self.__env.mongo.host = env_value

        env_value = os.getenv("MONGO_PORT")
        if env_value != None and env_value != "":
            self.__env.mongo.port = int(env_value)

    def __load_website_url(self):
        env_value = os.getenv("WEBSITE_URL")
        if env_value != None and env_value != "":
            self.__env.website_url = env_value


config = BotConfiguration()


def init(dir: str = ""):
    """
    初始化環境變數
    """
    global config, root_dir

    # Binding the root directory
    root_dir = dir

    # Check if the config file exists
    print("Try loading config.json...")
    if os.path.exists(JsonConfigLoader.config_file_name()):
        print('The "config.json" file is found. Try loading it...')
        loader = JsonConfigLoader(config)
        loader.load()
        print("Configurations are loaded.")
        return

    print('The "config.json" file is not found. Try loading environment variables...')
    loader = EnvironmentVariableLoader(config)
    loader.load()
    print("Configurations are loaded.")


def bot_token() -> str:
    """
    取得機器人的Token
    """
    return config.bot_token


def guild_id() -> int:
    """
    取得Discord伺服器的ID
    """
    return config.guild_id


def master_id() -> int | None:
    """
    取得Discord頻道管理員的使用者ID
    """
    return config.master_id


def dev_id() -> int | None:
    """
    取得機器人開發者的使用者ID
    """
    return config.dev_id


def clan(role_id: int) -> ClanConfig | None:
    """
    取得指定的戰隊設定
    """
    for clan in config.clans:
        if clan.role_id == role_id:
            return clan

    return None


def clans() -> list[ClanConfig]:
    """
    取得Discord頻道中與戰隊戰相關的身分組清單
    """
    # 回傳除了測試用的戰隊外的所有戰隊
    return [clan for clan in config.clans if clan.role_name != "test"]


def boss_health(boss_id: int) -> int | None:
    """
    取得指定的首領的滿血血量
    """
    if len(config.clans) == 0:
        return None

    for clan in config.clans:
        for channel in clan.boss_channels:
            if channel.id == boss_id:
                return channel.health

    return None


def mongo_user() -> str | None:
    """
    取得MongoDB的使用者名稱
    """
    if config.mongo == None:
        return None

    return config.mongo.user


def mongo_password() -> str | None:
    """
    取得MongoDB的使用者密碼
    """
    if config.mongo == None:
        return None

    return config.mongo.password


def mongo_protocol() -> str:
    """
    取得MongoDB的連接協定
    """
    if config.mongo == None:
        return "mongodb://"

    return config.mongo.protocol


def mongo_host() -> str | None:
    """
    取得MongoDB的主機名稱
    """
    if config.mongo == None:
        return None

    return config.mongo.host


def mongo_port() -> int | None:
    """
    取得MongoDB的連接埠號
    """
    if config.mongo == None:
        return None

    return config.mongo.port


def website_url() -> str | None:
    """
    取得戰隊戰作業製圖網站的URL
    """
    return config.website_url


def clan_battle_notification() -> ClanBattleNotificationConfig | None:
    """
    取得戰隊戰通知的設定
    """
    return config.clan_battle_notification


def bot_clan_id() -> int | None:
    """
    取得機器人戰隊的戰隊ID
    """
    return config.bot_clan_id
