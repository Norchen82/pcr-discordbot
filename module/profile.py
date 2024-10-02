# type: ignore
import pymongo
import discord

import module.cfg as cfg
import urllib.parse
import pickle


protocol = cfg.mongo_protocol()
host = cfg.mongo_host()
port = cfg.mongo_port()
user_name = cfg.mongo_user()
password = cfg.mongo_password()

connection_str = ""
if protocol == "mongodb+srv":
    connection_str = f"mongodb+srv://{user_name}:{password}@{host}"
elif protocol == "mongodb":
    connection_str = (
        f"mongodb://{user_name}:{urllib.parse.quote_plus(password)}@{host}:{port}"
    )

client: pymongo.MongoClient | None = None
db: pymongo.database.Database | None = None

if connection_str != "":
    client = pymongo.MongoClient(connection_str)
    db = client.bot


class Subscription:
    def __init__(
        self,
        type: str,
        player_id: str,
        player_name: str,
        arena: bool,
        grand_arena: bool,
        activity: bool,
    ):
        self.type = type
        self.player_id = player_id
        self.player_name = player_name
        self.arena = arena
        self.grand_arena = grand_arena
        self.activity = activity


class Profile:
    def __init__(
        self,
        id: int,
        subscriptions: list[Subscription] | None = None,
    ):
        self.id = id
        self.subscriptions = subscriptions


def add_subscription(user_id: int, subscription: Subscription):
    """
    啟用對指定玩家的競技場訂閱
    """
    if db is None:
        raise Exception("Connection to database failed.")

    profile = db.profiles.find_one({"_id": user_id})
    if profile is None:
        db.profiles.insert_one(
            {"_id": user_id, "subscriptions": [dump_subscription(subscription)]}
        )
        return

    subscriptions = profile.get("subscriptions", [])
    for index, sub in enumerate(subscriptions):
        if (
            sub["type"] == subscription.type
            and sub["playerId"] == subscription.player_id
        ):
            subscriptions[index]["arena"] = subscription.arena
            subscriptions[index]["grandArena"] = subscription.grand_arena
            subscriptions[index]["activity"] = subscription.activity
            db.profiles.update_one(
                {"_id": user_id},
                {"$set": {"subscriptions": subscriptions}},
            )
            return

    subscriptions.append(dump_subscription(subscription))
    db.profiles.update_one(
        {"_id": user_id},
        {"$set": {"subscriptions": subscriptions}},
    )


def delete_subscription(user_id: int, subscription: Subscription):
    """
    取消對指定玩家的競技場訂閱
    """
    if db is None:
        raise Exception("Connection to database failed.")

    profile = db.profiles.find_one({"_id": user_id})
    if profile is None:
        return

    subscriptions = profile.get("subscriptions", [])
    for index, sub in enumerate(subscriptions):
        if (
            sub["type"] == subscription.type
            and sub["playerId"] == subscription.player_id
        ):
            del subscriptions[index]
            db.profiles.update_one(
                {"_id": user_id},
                {"$set": {"subscriptions": subscriptions}},
            )
            return


def get_profile(user_id: int) -> Profile | None:
    """
    取得使用者的檔案
    """
    if db is None:
        raise Exception("Connection to database failed.")

    profile = db.profiles.find_one({"_id": user_id})
    if profile is None:
        return None

    return load_profile(profile)


def get_profiles():
    """
    取得所有使用者的檔案
    """
    if db is None:
        raise Exception("Connection to database failed.")

    return [load_profile(profile) for profile in db.profiles.find()]


def load_profile(profile: dict) -> Profile:
    return Profile(
        id=profile["_id"],
        subscriptions=load_subscriptions(profile.get("subscriptions", [])),
    )


def load_subscriptions(subscriptions: list[dict]) -> list[Subscription]:
    return [
        Subscription(
            type=sub["type"],
            player_id=sub["playerId"],
            player_name=sub["playerName"],
            arena=sub["arena"],
            grand_arena=sub["grandArena"],
            activity=sub["activity"],
        )
        for sub in subscriptions
    ]


def dump_subscription(subscription: Subscription) -> dict:
    return {
        "type": subscription.type,
        "playerId": subscription.player_id,
        "playerName": subscription.player_name,
        "arena": subscription.arena,
        "grandArena": subscription.grand_arena,
        "activity": subscription.activity,
    }
