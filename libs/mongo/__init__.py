from typing import Any
import module.cfg as cfg
import urllib.parse
from pymongo import MongoClient, database

protocol = cfg.mongo_protocol()
host = cfg.mongo_host()
port = cfg.mongo_port()
user_name = cfg.mongo_user()
password = cfg.mongo_password()

if host is None:
    raise Exception("MongoDB host is not set")
if port is None:
    raise Exception("MongoDB port is not set")
if user_name is None:
    raise Exception("MongoDB username is not set")
if password is None:
    raise Exception("MongoDB password is not set")

connection_str = ""
if protocol == "mongodb+srv":
    connection_str = f"mongodb+srv://{user_name}:{password}@{host}"
elif protocol == "mongodb":
    connection_str = (
        f"mongodb://{user_name}:{urllib.parse.quote_plus(password)}@{host}:{port}"
    )

client: MongoClient[Any] | None = None
db: database.Database[Any] | None = None

if connection_str != "":
    client = MongoClient(connection_str)
    db = client.bot
