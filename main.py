#!/usr/bin/env python3

"""The main file of Amélie that needs to be run directly.

It's the entry point for other modules.
"""

from __future__ import annotations

import asyncio
import json
import pkgutil
from itertools import cycle
from pathlib import Path
from typing import NoReturn

import discord
from discord.ext import commands, tasks

import cogs
from core import terminal
from core.database import initialize_tables
from core.log_handler import logger_setup

BOT = commands.Bot(
    command_prefix=".",
    intents=discord.Intents.all(),
    case_insensitive=True,
    help_command=None,
)  # Bot's instance

# Read the stored token from config.json
with Path("config.json").open("r") as file:
    CONFIG = json.load(file)

logger = logger_setup(__name__)


async def _cog_loader() -> None:
    """Load all cogs from cog directory."""
    succeed: list[str] = []
    failed: list[str] = []
    for module_info in pkgutil.walk_packages(cogs.__path__, cogs.__name__ + "."):
        # if it's a directory
        if module_info.ispkg:
            continue

        try:
            await BOT.load_extension(module_info.name)  # loads the cog
            succeed.append(module_info.name.split(".")[-1])
        except:
            logger.exception(
                "❌ %s couldn't be loaded: ",
                module_info.name.split(".")[-1],
            )
            failed.append(module_info.name.split(".")[-1])

            raise

    if failed:
        logger.error("%s cogs failed to get loaded ❌", failed)
    logger.info("%s cogs have been loaded ☑️", succeed)


async def _terminal_listener() -> NoReturn:
    """Start listening to terminal commands."""
    loop = asyncio.get_running_loop()
    term = terminal.Terminal(BOT)
    while True:
        cmd = await loop.run_in_executor(None, input, ">> ")
        await term.command(cmd)


@BOT.event
async def on_ready() -> None:
    """Print a message when bot is ready."""
    logger.info("--------------\nWe have logged in as %s ✅", BOT.user)

    # runs the terminal listener for in-line commands
    BOT.loop.create_task(_terminal_listener())

    bot_status_change.start()


# Amelie's different status
bot_status = cycle([
    discord.Activity(
        type=discord.ActivityType.playing,
        name="Fortnite",
        platform="PS4",
    ),
    discord.Activity(
        type=discord.ActivityType.playing,
        name="playing with your server",
    ),
    discord.Activity(
        type=discord.ActivityType.listening,
        name="listening to your complaints",
    ),
    discord.Activity(type=discord.ActivityType.watching, name="watching reels"),
    discord.Activity(type=discord.ActivityType.playing, name="lanat be in zendegi"),
])


@tasks.loop(minutes=2)
async def bot_status_change() -> None:
    """Change bot status message every 2 minutes."""
    await BOT.change_presence(activity=next(bot_status))


async def _main() -> None:
    # initializes the tables if needed
    await initialize_tables()
    logger.info("💾 Database tables initialization complete.")

    async with BOT:
        await _cog_loader()  # loads the cogs
        try:
            await BOT.start(CONFIG["TOKEN"])  # starts the bot
        except:
            logger.critical("❌ Failed to start the bot:", exc_info=True)
            raise


if __name__ == "__main__":
    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        logger.info("\n--------------\nThe Bot has been shut down. ⏹️")
