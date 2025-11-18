import discord
from discord.ext import commands, tasks
import json
import asyncio
import os
from itertools import cycle
from database import setup

intents = discord.Intents.all()
bot = commands.Bot(command_prefix = '.', intents = intents, case_insensitive = True, help_command = None) #defines bot object

@bot.event
async def on_ready():
        #prints a message when bot is ready
        print(
            "--------------"
            f"\nWe have logged in as {bot.user} ✅"
        )
        
        botStatusChange.start() #starts changing bot statuses

#different possible bot status
bot_status = cycle([
    discord.Activity(type = discord.ActivityType.playing, name = "Fortnite", platform = "PS4"),
    discord.Activity(type = discord.ActivityType.playing, name = "playing with your server"),
    discord.Activity(type = discord.ActivityType.listening, name = "listening to your complaints"),
    discord.Activity(type = discord.ActivityType.watching, name = "watching reels"),
    discord.Activity(type = discord.ActivityType.playing, name = "lanat be in zendegi")
])
#changes bot status message every 2 minutes
@tasks.loop(minutes = 2)
async def botStatusChange():
    await bot.change_presence(activity = next(bot_status))

#cogloader function
async def cogsload():
    success: list[str] = []
    for root, _, files in os.walk("./cogs"):
        for file in files:
            #must be .py
            if not file.endswith(".py"):
                continue

            #skips package initializers
            if file == "__init__.py":
                continue

            #Builds cog path
            #./cogs/moderation/kick.py  →  cogs.moderation.kick
            rel_path = os.path.join(root, file)
            module = rel_path.replace("\\", "/")[:-3]
            if module.startswith("./"):
                module = module[2:]
            module = module.replace("/", ".")

            try:
                await bot.load_extension(module) #loads cog
                success.append(module.split(".")[-1])
            except Exception as e:
                print(f"❌ Failed to load {module}: {e}")
    print(f"{success} cogs loaded ☑️")

#reads the stored token from config.json
with open("config.json") as file:
    config = json.load(file)

async def main():
    await setup() #sets up the database
    print("💾 Database has been connected successfully.")

    async with bot:
        await cogsload() #loads the cogs
        try:
            await bot.start(config["TOKEN"]) #starts the bot
        except Exception as e:
            print(f"❌ Failed to start the bot: {e}")

asyncio.run(main())