import discord
from discord.ext import commands
import json
import time

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='.', intents=intents)

#print a message when bot is ready
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user} ✅')


#ping command
@bot.command(name = "ping")
async def ping(ctx):
    pings = []
    pingNumbers = 4

    msg = await ctx.reply("pinging...")

    ws = bot.latency * 1000

    #starts pinging n times
    for i in range(pingNumbers):
        start = time.perf_counter()
        await msg.edit(content = f"ping {i + 1}..")
        end = time.perf_counter()

        msg_latency = (end - start) * 1000
        pings.append(msg_latency) #stores the nth ping in a list

    avg = sum(pings) / pingNumbers
    min = min(pings)
    max = max(pings)
    await msg.edit(content = (
        "Pong! 🏓\n"
        f"📡WebSocket Latency: `{ws:.2f} ms`\n"
        f"🌐REST Latency: `{avg:.2f} ms`\n"
        f"Min: `{min:.2f} ms` | Max: `{max:.2f} ms`"
    ))


#embed message command
@bot.command(name = "embed")
async def embed(ctx, *, args):
    pass


#reading the stored token from config.json
with open("config.json") as file:
    config = json.load(file)

#runs the bot
bot.run(config["TOKEN"])