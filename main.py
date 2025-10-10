import discord
from discord.ext import commands
import json
import asyncio
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='.', intents=intents)

#reading the stored token from config.json
with open("config.json") as file:
    config = json.load(file)

async def cogsload():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"{filename[:-3]} cog loaded ☑️")
            except Exception as e:
                print(f"❌ Failed to load {filename[:-3]} cog: {e}")

async def main():
    async with bot:
        await cogsload() #loads the cogs
        try:
            await bot.start(config["TOKEN"]) #starts the bot
        except Exception as e:
            print(f"❌ Failed to start the bot: {e}")

asyncio.run(main())