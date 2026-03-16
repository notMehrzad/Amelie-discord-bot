import discord
from discord.ext import commands, tasks
import json
import asyncio
import pkgutil
import cogs
import terminal
from itertools import cycle
from database import db
from logHandler import loggerSetup

bot = commands.Bot(
    command_prefix=".",
    intents=discord.Intents.all(),
    case_insensitive=True,
    help_command=None,
)  # defines the bot instance


# cogloader function
async def cogLoader():
    succeed: list[str] = []
    failed: list[str] = []
    for modulInfo in pkgutil.walk_packages(cogs.__path__, cogs.__name__ + "."):
        # if it's a directory
        if modulInfo.ispkg:
            continue

        try:
            await bot.load_extension(modulInfo.name)  # loads the cog
            succeed.append(modulInfo.name.split(".")[-1])
        except Exception:
            logger.exception(f"❌ {modulInfo.name.split(".")[-1]} couldn't be loaded: ")
            failed.append(modulInfo.name.split(".")[-1])

    if failed:
        print(f"{failed} cogs failed to get loaded ❌")
    print(f"{succeed} cogs have been loaded ☑️")


async def terminal_listener():
    loop = asyncio.get_running_loop()
    term = terminal.Terminal(bot)
    while True:
        cmd = await loop.run_in_executor(None, input, ">> ")
        await term.command(cmd)


@bot.event
async def on_ready():
    print(
        "--------------" f"\nWe have logged in as {bot.user} ✅"
    )  # prints a message when bot is ready
    bot.loop.create_task(
        terminal_listener()
    )  # runs the terminal listener for in-line commands
    botStatusChange.start()  # starts changing bot statuses


# different possible bot status
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
async def botStatusChange():
    await bot.change_presence(activity=next(bot_status))


# reads the stored token from config.json
with open("config.json") as file:
    config = json.load(file)


async def main():
    # sets up the initial logger
    global logger
    logger = loggerSetup(__name__)

    await db.tableInitialize()  # initializes the tables if needed
    print("💾 Database works fine.")

    async with bot:
        await cogLoader()  # loads the cogs
        try:
            await bot.start(config["TOKEN"])  # starts the bot
        except Exception:
            logger.exception(f"❌ Failed to start the bot: ")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n--------------")
        print(f"The Bot has been shut down. ⏹️")
