import discord
from discord.ext import commands
import json

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='.', intents=intents)

#print a message when bot is ready
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user} ✅')

#registering the ping command
@bot.command(name = "ping")
async def ping(ctx):
    await ctx.reply("Pong!")


#reading the stored token from config.json
with open("config.json") as file:
    config = json.load(file)

#runs the bot
bot.run(config["TOKEN"])