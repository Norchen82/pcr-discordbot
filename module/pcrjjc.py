import json
import os
from asyncio import Lock
from json import load
from os.path import join, exists
from module.cfg import root_dir

from libs.pcrjjc.pcrclient import PcrClient, ApiException, default_headers
from libs.pcrjjc.playerpref import decrypt_xml

from module import cfg

# region ========== ↓ ↓ ↓ 配置读取 ↓ ↓ ↓ ==========

# 读取绑定配置
old_config = join(root_dir, "binds.json")
config = join(root_dir, "binds_v2.json")
root: dict[str, object] = {"global_push": True, "arena_bind": {}}
if exists(config):
    with open(config) as fp:
        root = load(fp)
binds = root["arena_bind"]

# 读取代理配置
with open(join(root_dir, "account.json")) as fp:
    pInfo = load(fp)

# 一些变量初始化
client = None

# 设置异步锁保证线程安全
lck = Lock()
captcha_lck = Lock()
qLck = Lock()

# 戰隊ID，要有這個ID才能查詢戰隊排名
clan_id = cfg.bot_clan_id()

# 全局缓存的client登陆 | 减少协议握手次数
first_client_cache = None
other_client_cache = None

# endregion ========== ↑ ↑ ↑ 配置读取 ↑ ↑ ↑ ==========

# region ========== ↓ ↓ ↓ 启动时检查文件 ↓ ↓ ↓ ==========

# 生成一份旧版headers文件
header_path = os.path.join(root_dir, "headers.json")
if not os.path.exists(header_path):
    with open(header_path, "w", encoding="UTF-8") as f:
        json.dump(default_headers, f, indent=4, ensure_ascii=False)

# 头像框设置文件，默认彩色
current_dir = os.path.join(root_dir, "frame.json")
if not os.path.exists(current_dir):
    data: dict[str, object] = {"default_frame": "color.png", "customize": {}}
    with open(current_dir, "w", encoding="UTF-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# 2023-05-10 合服 | 如果检测到旧配置且没有新配置，就将其移入新配置文件
if os.path.exists(old_config) and not os.path.exists(config):
    with open(old_config, "r", encoding="UTF-8") as file0:
        config_data = dict(json.load(file0))
    bind_data = config_data.get("arena_bind", {})
    for user_id_str in list(bind_data.keys()):
        bind_data_info = bind_data.get(user_id_str, {})

        game_id_str = bind_data_info.get("id", "")
        cx_str = bind_data_info.get("cx", "")
        bind_data_info["id"] = cx_str + game_id_str
        bind_data[user_id_str] = bind_data_info
    config_data["arena_bind"] = bind_data
    config_data["global_push"] = True
    with open(config, "w", encoding="UTF-8") as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)
    root = config_data
    binds = root["arena_bind"]


# endregion ========== ↑ ↑ ↑ 启动时检查文件 ↑ ↑ ↑ ==========

# region ========== ↓ ↓ ↓ 读取 & 校验 ↓ ↓ ↓ ==========


# 查询配置文件是否存在
def judge_file(cx_id: int):
    cx = "first" if cx_id == 1 else "other"
    cx_path = os.path.join(
        root_dir, f"{cx}_tw.sonet.princessconnect.v2.playerprefs.xml"
    )
    if os.path.exists(cx_path):
        return True
    else:
        return False


# 获取配置文件
def get_client():
    global first_client_cache, other_client_cache

    ac_info_first = {"admin": ""}
    ac_info_other = {"admin": ""}

    # 1服
    if first_client_cache is None:
        if judge_file(1):
            ac_info_first = decrypt_xml(
                join(root_dir, "first_tw.sonet.princessconnect.v2.playerprefs.xml")
            )
            client_first = PcrClient(
                ac_info_first["UDID"],
                ac_info_first["SHORT_UDID"],
                ac_info_first["VIEWER_ID"],
                ac_info_first["TW_SERVER_ID"],
                pInfo["proxy"],
            )
        else:
            client_first = None
        first_client_cache = client_first

    # 其他服
    if other_client_cache is None:
        if judge_file(0):
            ac_info_other = decrypt_xml(
                join(root_dir, "other_tw.sonet.princessconnect.v2.playerprefs.xml")
            )
            client_other = PcrClient(
                ac_info_other["UDID"],
                ac_info_other["SHORT_UDID"],
                ac_info_other["VIEWER_ID"],
                ac_info_other["TW_SERVER_ID"],
                pInfo["proxy"],
            )
        else:
            client_other = None
        other_client_cache = client_other

    return first_client_cache, other_client_cache, ac_info_first, ac_info_other


# 查询个人信息
async def query_profile(uid: str) -> dict[str, object]:
    client_first, client_other, _, _ = get_client()
    cur_client = client_first if uid.startswith("1") else client_other
    if cur_client is None:
        return {"lack share_prefs": {}}
    async with qLck:
        try:
            await cur_client.callapi("/load/index", {"carrier": "Android"})
        except ApiException as _:
            # sv.logger.error("登录超时或失败，将尝试一次重新登录，正在重新登录...")
            print("登入超時或失敗，將嘗試一次重新登入，正在重新登入...")
        while cur_client.shouldLogin:
            await cur_client.login()
        res = await cur_client.callapi(
            "/profile/get_profile", {"target_viewer_id": int(uid)}
        )
        return res


# 查询个人信息
async def query_clan_ranking(page: int) -> object:
    _, client_other, _, _ = get_client()
    cur_client = client_other
    if cur_client is None:
        return {"lack share_prefs": {}}
    async with qLck:
        try:
            await cur_client.callapi("/load/index", {"carrier": "Android"})
        except ApiException as _:
            # sv.logger.error("登录超时或失败，将尝试一次重新登录，正在重新登录...")
            print("登入超時或失敗，將嘗試一次重新登入，正在重新登入...")
        while cur_client.shouldLogin:
            await cur_client.login()
        res = await cur_client.callapi(
            "/clan_battle/period_ranking",
            {
                "clan_id": clan_id,
                "clan_battle_id": -1,
                "period": -1,
                "month": 0,
                "page": page,
                "is_my_clan": 0,
                "is_first": 1,
            },
        )
        return res


async def judge_uid(uid_str: str) -> str | None:
    # 校验数字
    try:
        int(uid_str)
    except TypeError as _:
        return "uid错误，需要10位纯数字，您输入了[" + str(len(uid_str)) + "]"

    if len(uid_str) != 10:
        return "uid长度错误，需要10位数字，您输入了[" + str(len(uid_str)) + "]"

    # 校验服务器
    cx = uid_str[:1]
    if cx not in ["1", "2", "3", "4"]:
        return "uid校验出错，您输入了[" + str(len(uid_str)) + "]"

    return None


# endregion ========== ↑ ↑ ↑ 读取 & 校验 ↑ ↑ ↑ ==========
