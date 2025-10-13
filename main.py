import discord
from discord.ext import commands, tasks
import json
import asyncio
import os
from itertools import cycle

#defining bot object
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='.', intents=intents)

#defining bot status
bot_status = cycle(["drowned in nothingness.", "lanat be in zendegi", "Fortnite"])
@tasks.loop(minutes = 2)
async def botStatusChange():
    await bot.change_presence(activity = discord.Game(next(bot_status)))

@bot.event
async def on_ready():
        #prints a message when bot is ready
        print(
            "--------------"
            f"\nWe have logged in as {bot.user} ✅"
        )
        #starts changing bot statuses
        botStatusChange.start()

async def cogsload():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"{filename[:-3]} cog loaded ☑️")

            except Exception as e:
                print(f"❌ Failed to load {filename[:-3]} cog: {e}")


#reads the stored token from config.json
with open("config.json") as file:
    config = json.load(file)

async def main():
    async with bot:
        await cogsload() #loads the cogs
        try:
            await bot.start(config["TOKEN"]) #starts the bot

        except Exception as e:
            print(f"❌ Failed to start the bot: {e}")

asyncio.run(main())