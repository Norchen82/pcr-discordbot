from module import cfg
from os.path import dirname

cfg.init(dirname(__file__))

import bot
import commands
from cronjobs import jjc_notify, clan_battle_notify

if __name__ == "__main__":
    bot.init(commands.init)
    bot.client.run(cfg.bot_token())
