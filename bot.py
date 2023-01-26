import datetime
import logging
import os
from pathlib import Path
import platform

import discord
import wavelink
from discord.ext import commands

import config
from utils import db


class CustomFormatter(logging.Formatter):
    def format(self, record):
        log_fmt = FORMATS[record.levelno]
        formatter = logging.Formatter(log_fmt, style="{", datefmt="%d-%m-%y %H:%M:%S")
        return formatter.format(record)


FMT = "[{levelname:^9}] [{asctime}] [{name}] [{module}:{lineno}] : {message}"
FORMATS = {
    logging.DEBUG: f"\33[37m{FMT}\33[0m",
    logging.INFO: f"\33[36m{FMT}\33[0m",
    logging.WARNING: f"\33[33m{FMT}\33[0m",
    logging.ERROR: f"\33[31m{FMT}\33[0m",
    logging.CRITICAL: f"\33[1m\33[31m{FMT}\33[0m",
}


log = logging.getLogger("mainLog")
log.setLevel(logging.DEBUG)
if not Path("logs").exists():
    os.mkdir("logs")
if len(os.listdir("logs")) >= 7:
    for file in os.listdir("logs"):
        os.remove("logs/" + file)
        break

log_path = f"logs/{log.name} {datetime.datetime.now().strftime('%Y-%m-%d')}.log"
file_format = logging.Formatter(
    "[{levelname:^9}] [{asctime}] [{name}] [{module:^4}:{lineno:^4}] | {message}",
    style="{",
    datefmt="%d-%m-%y %H:%M:%S",
)


file_handler = logging.FileHandler(log_path, "w")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(file_format)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(CustomFormatter())

log.addHandler(file_handler)
log.addHandler(console_handler)


class AnyClient(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        log.info(
            f"Bot initialized with Pycord Version {discord.__version__} and Python Version {platform.python_version()}"
        )

        self.views_added = False
        self.db_setup = False
        self.nodes_connected = False

    async def on_ready(self):
        if not self.views_added:
            # self.add_view(AnyView(self))
            self.views_added = True
            log.info("Added persistent views successfully")

        if not self.db_setup:
            self.db_setup = await db.setup_dbs()

        if not self.nodes_connected:
            """Connect to our Lavalink nodes."""
            await self.wait_until_ready()
            await wavelink.NodePool.create_node(bot=self, host="127.0.0.1", port=2333, password="youshallnotpass")
            self.nodes_connected = True
            log.info("Connected to Lavalink")


client = AnyClient(
    command_prefix=commands.when_mentioned,
    case_insensitive=True,
    strip_after_prefix=True,
    intents=discord.Intents.all(),
    debug_guilds=config.GUILDS,
    activity=discord.Activity(type=discord.ActivityType.watching, name="you"),
    state=discord.Status.online,
)


if __name__ == "__main__":
    client.load_extensions("cogs.music", "cogs.settings")
    client.run(config.TOKEN)
