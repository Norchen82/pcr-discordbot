import asyncio
import random
import time
import discord
import math
import bot

from module import (
    profile,
    pcrjjc,
)

arena_cache: dict[str, tuple[int, int]] = {}
login_cache: dict[str, int] = {}


async def on_jjc_notify():
    for p in profile.get_profiles():
        if p.subscriptions is None:
            continue

        user = bot.client.get_user(p.id)
        if user is None:
            continue

        for sub in p.subscriptions:
            try:
                uid = sub.player_id
                print(f"正在查詢玩家{uid}的資料")
                res = await pcrjjc.query_profile(uid)
                if "lack share_prefs" in res:
                    print(f"由於缺少該伺服器的設定文件，已跳過id: {uid}")
                    continue

                if sub.arena or sub.grand_arena:
                    await notify_arena(
                        user,
                        res,
                        sub.arena,
                        sub.grand_arena,
                    )

                if sub.activity:
                    await notify_activity(user, res)

                # 防止被判斷為機器人，隨機等待數秒後再進行下一次查詢
                await asyncio.sleep(random.randrange(1, 5, 1))

            except pcrjjc.ApiException as e:
                print(f"检查出错" + str(e))

            except Exception as e:
                print(f"检查出错" + str(e))


async def notify_arena(
    user: discord.User,
    user_data: dict[str, object],
    arena_on: bool,
    grand_arena_on: bool,
):
    global arena_cache

    player_id: str = user_data["user_info"]["viewer_id"]
    player_name: str = user_data["user_info"]["user_name"]
    ranks: tuple[int, int] = (
        user_data["user_info"]["arena_rank"],
        user_data["user_info"]["grand_arena_rank"],
    )

    cache_key = f"ranks_{player_id}"
    if cache_key not in arena_cache:
        arena_cache[cache_key] = ranks
        return

    prev = arena_cache[cache_key]
    arena_cache[cache_key] = ranks

    print(f"玩家{player_name}競技場排名的變化：{prev} -> {ranks}")

    if arena_on:
        prev_arena_rank = int(prev[0])
        curr_arena_rank = int(ranks[0])
        if curr_arena_rank > prev_arena_rank:
            await user.send(
                f"玩家**{player_name}**的１v１競技場名次 {prev_arena_rank} -> {curr_arena_rank}  ▼{curr_arena_rank - prev_arena_rank}"
            )

    if grand_arena_on:
        prev_grand_arena_rank = int(prev[1])
        curr_grand_arena_rank = int(ranks[1])
        if curr_grand_arena_rank > prev_grand_arena_rank:
            await user.send(
                f"玩家**{player_name}**的３v３競技場名次 {prev_grand_arena_rank} -> {curr_grand_arena_rank}  ▼{curr_grand_arena_rank - prev_grand_arena_rank}"
            )


async def notify_activity(
    user: discord.User,
    user_data: dict[str, dict[str, str]],
):
    global login_cache

    player_id = user_data["user_info"]["viewer_id"]
    player_name = user_data["user_info"]["user_name"]

    last_login_time = int(user_data["user_info"]["last_login_time"])
    cache_key = f"activity_{player_id}"
    if cache_key not in login_cache:
        login_cache[cache_key] = last_login_time
        return

    prev_login_time = login_cache[cache_key]
    login_cache[cache_key] = last_login_time

    print(f"玩家{player_name}上線時間的變化：{prev_login_time} -> {last_login_time}")

    if last_login_time - prev_login_time > 3600:
        since = int(time.time()) - last_login_time
        since_str = ""
        if since < 60:
            since_str = f"{since}秒"
        elif since < 3600:
            minute = math.floor(since / 60)
            second = since % 60
            since_str = f"{minute}分{second}秒"

        await user.send(f"玩家**{player_name}**已於{since_str}前上線。")
        return


bot.on_jjc_notify = on_jjc_notify
