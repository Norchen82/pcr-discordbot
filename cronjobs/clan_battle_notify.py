import bot
import pytz
import random
import calendar
import asyncio
from datetime import datetime, timedelta
from module import cfg
from module.pcrjjc import query_clan_ranking
from bot import client
import discord

last_clan_ranking_times: dict[int, datetime] = {}


async def on_clan_battle_notify():
    global last_clan_ranking_times

    config = cfg.clan_battle_notification()
    if config == None:
        print("未設定戰隊戰通知")
        return

    exe_time = datetime.now(pytz.timezone("ROC"))

    clans: list[cfg.ClanBattleNotificationConfigClan] = []
    for clan in config.clans:
        if (
            not clan.update_on_start
            and clan.leader_viewer_id not in last_clan_ranking_times
        ):
            last_clan_ranking_times[clan.leader_viewer_id] = exe_time
            continue

        if need_update_clan_ranking(clan, exe_time) or need_notify_clan_ranking(
            clan, exe_time
        ):
            clans.append(clan)

    if len(clans) == 0:
        return

    await search_clan_ranking(clans, exe_time)


def need_update_clan_ranking(clan: cfg.ClanBattleNotificationConfigClan, now: datetime):
    global last_clan_ranking_times

    if clan.leader_viewer_id not in last_clan_ranking_times:
        return True

    last_time = last_clan_ranking_times[clan.leader_viewer_id]
    diff = now - last_time

    # 判斷是否為戰隊戰期間
    _, number_of_days = calendar.monthrange(now.year, now.month)
    start_time = datetime(
        now.year, now.month, number_of_days - 4, 5, 0, 0, tzinfo=pytz.timezone("ROC")
    )
    end_time = datetime(
        now.year, now.month + 1, 1, 0, 0, 0, tzinfo=pytz.timezone("ROC")
    )
    if not (start_time <= now < end_time):
        return False

    if diff.total_seconds() >= 1800:
        return True

    if time_period_group(last_time) != time_period_group(now):
        return True

    return False


def need_notify_clan_ranking(clan: cfg.ClanBattleNotificationConfigClan, now: datetime):
    global last_clan_ranking_times

    if clan.leader_viewer_id not in last_clan_ranking_times:
        return False

    last_time = last_clan_ranking_times[clan.leader_viewer_id]
    diff = now - last_time

    # 判斷是否為戰隊戰期間
    _, number_of_days = calendar.monthrange(now.year, now.month)
    start_time = datetime(
        now.year, now.month, number_of_days - 4, 5, 0, 0, tzinfo=pytz.timezone("ROC")
    )
    end_time = datetime(
        now.year, now.month + 1, 1, 0, 0, 0, tzinfo=pytz.timezone("ROC")
    )
    if not (start_time <= now < end_time):
        return False

    # 如果是最後一天，強制在23:20跟23:50推送
    force_push = now.day == number_of_days and now.hour == 23 and now.minute >= 20

    if force_push or clan.cron is None:
        if diff.total_seconds() >= 1800:
            return True

        if time_period_group(last_time) != time_period_group(now):
            return True

        return False
    else:
        parts = clan.cron.split(" ")
        hours = int(parts[0])
        minutes = int(parts[1])

        last_time_rounded = last_time.replace(minute=0, second=0, microsecond=0)

        target_time = last_time_rounded.replace(hour=hours, minute=minutes)
        if target_time <= last_time:
            target_time += timedelta(days=1)

        if now >= target_time:
            return True

        return False


def time_period_group(time: datetime) -> int:
    if 20 <= time.minute < 50:
        return 20
    else:
        return 50


async def search_clan_ranking(
    clans: list[cfg.ClanBattleNotificationConfigClan], now: datetime
):
    global last_clan_ranking_times
    try:
        counter = 0

        for page in range(5, 21):
            res = await query_clan_ranking(page)
            ranking = res["period_ranking"]
            for rank in ranking:
                for clan in clans:
                    if rank["leader_viewer_id"] == clan.leader_viewer_id:
                        minute = time_period_group(now)
                        hour = now.hour if now.minute >= 20 else now.hour - 1
                        if hour < 0:
                            hour += 24

                        time_group_str = f"{hour:02d}:{minute:02d}"

                        guild = client.get_guild(clan.guild_id)
                        if guild == None:
                            print(f"找不到guild_id: {clan.guild_id}")
                            continue

                        if (
                            clan.polling_channel_id != None
                            and clan.polling_channel_name != None
                        ):
                            await modify_polling_channel_name(
                                guild,
                                clan.polling_channel_id,
                                clan.polling_channel_name,
                                rank["rank"],
                            )

                        if not need_notify_clan_ranking(clan, now):
                            continue

                        if clan.channel_id != None:
                            await guild.get_channel(clan.channel_id).send(
                                f"戰隊**{rank['clan_name']}**截至{now.strftime('%Y-%m-%d')} {time_group_str}的戰隊戰排名為{rank['rank']}",
                            )

                        if clan.thread_id != None:
                            await guild.get_thread(clan.thread_id).send(
                                f"戰隊**{rank['clan_name']}**截至{now.strftime('%Y-%m-%d')} {time_group_str}的戰隊戰排名為{rank['rank']}",
                            )

                        last_clan_ranking_times[clan.leader_viewer_id] = now
                        counter += 1

                if counter == len(clans):
                    return

            await asyncio.sleep(0.5 + random.uniform(0, 1))

    except Exception as err:
        print(err)


async def modify_polling_channel_name(
    guild: discord.Guild, channel_id: int, format: str, rank: int
):
    channel = guild.get_channel(channel_id)
    if channel == None:
        print(f"找不到polling_channel_id: {channel_id}")
        return

    name = format.replace("{rank}", str(rank))
    await channel.edit(name=name)


bot.on_clan_battle_notify = on_clan_battle_notify
