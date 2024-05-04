from module import cfg

cfg.init()

import bot
import commands

if __name__ == "__main__":
    bot.init(commands.init)
    bot.client.run(cfg.bot_token())
