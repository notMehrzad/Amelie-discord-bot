#!usr/bin/env python3
"""The main file of Amelie that needs to be run directly.
It's the entry point for other modules.
"""

import asyncio
import json
import pkgutil
import terminal
from itertools import cycle

import discord
from discord.ext import commands, tasks

import cogs
from core.bank import ACCOUNT_TABLE, TRANSACTION_TABLE
from core.database import tableInitialize
from logHandler import loggerSetup

BOT = commands.Bot(
    command_prefix=".",
    intents=discord.Intents.all(),
    case_insensitive=True,
    help_command=None,
)  # bot's instance

# reads the stored token from config.json
with open("config.json") as file:
    CONFIG = json.load(file)

logger = loggerSetup(__name__)


async def _cogLoader():
    """Loads all the cogs from the cog directory."""

    succeed: list[str] = []
    failed: list[str] = []
    for modulInfo in pkgutil.walk_packages(cogs.__path__, cogs.__name__ + "."):
        # if it's a directory
        if modulInfo.ispkg:
            continue

        try:
            await BOT.load_extension(modulInfo.name)  # loads the cog
            succeed.append(modulInfo.name.split(".")[-1])
        except Exception:
            logger.exception(f"❌ {modulInfo.name.split(".")[-1]} couldn't be loaded: ")
            failed.append(modulInfo.name.split(".")[-1])

    if failed:
        logger.error(f"{failed} cogs failed to get loaded ❌")
    logger.info(f"{succeed} cogs have been loaded ☑️")


async def _terminal_listener():
    """Starts listening to terminal commands."""

    loop = asyncio.get_running_loop()
    term = terminal.Terminal(BOT)
    while True:
        cmd = await loop.run_in_executor(None, input, ">> ")
        await term.command(cmd)


@BOT.event
async def on_ready():
    logger.info(
        "--------------" f"\nWe have logged in as {BOT.user} ✅"
    )  # prints a message when bot is ready
    BOT.loop.create_task(
        _terminal_listener()
    )  # runs the terminal listener for in-line commands
    _botStatusChange.start()  # starts changing bot statuses


# Amelie's different status
bot_status = cycle(
    [
        discord.Activity(
            type=discord.ActivityType.playing, name="Fortnite", platform="PS4"
        ),
        discord.Activity(
            type=discord.ActivityType.playing, name="playing with your server"
        ),
        discord.Activity(
            type=discord.ActivityType.listening, name="listening to your complaints"
        ),
        discord.Activity(type=discord.ActivityType.watching, name="watching reels"),
        discord.Activity(type=discord.ActivityType.playing, name="lanat be in zendegi"),
    ]
)


# changes bot status message every 2 minutes
@tasks.loop(minutes=2)
async def _botStatusChange():
    await BOT.change_presence(activity=next(bot_status))


async def _main():
    """The entry point."""

    # initializes the tables if needed
    await tableInitialize(ACCOUNT_TABLE, TRANSACTION_TABLE)
    logger.info("💾 Database works fine.")

    async with BOT:
        await _cogLoader()  # loads the cogs
        try:
            await BOT.start(CONFIG["TOKEN"])  # starts the bot
        except Exception:
            logger.critical(f"❌ Failed to start the bot:", exc_info=True)


if __name__ == "__main__":
    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        logger.info("\n--------------" f"\nThe Bot has been shut down. ⏹️")
