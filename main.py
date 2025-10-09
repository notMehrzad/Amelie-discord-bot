import discord
from discord.ext import commands
import json
import time
import datetime

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

    ws = bot.latency * 1000 #getting websocket latency

    #starts pinging n times
    for i in range(pingNumbers):
        start = time.perf_counter()
        await msg.edit(content = f"ping {i + 1}..")
        end = time.perf_counter()

        msg_latency = (end - start) * 1000
        pings.append(msg_latency) #stores the nth ping in a list

    avg = sum(pings) / pingNumbers #getting REST latency
    minping = min(pings)
    maxping = max(pings)

    #defining color based on ws ping strength
    if ws <= 100:
        color = discord.Color.from_str("#00ff59") #green
    elif ws <= 200:
        color = discord.Color.from_str("#ffff00") #yellow
    elif ws <= 400:
        color = discord.Color.from_str("#ffab00") #orange
    else:
        color = discord.Color.from_str("#ff3800") #red

    #defining the result embed
    embed = discord.Embed(
        color = color,
        title = "Pong! 🏓",
        description = (
            f"📡WebSocket: `{ws:.2f} ms`\n"
            f"🌐REST: `{avg:.2f} ms`\n\n"
            f"Min: `{minping:.2f} ms` | Max: `{maxping:.2f} ms`"
        ),
        timestamp = datetime.datetime.now(datetime.UTC)
    ).set_footer(text = f"requested by {ctx.author.name}")

    await msg.edit(content = None, embed = embed)


#embed message command
@bot.command(name = "embed")
async def embed(ctx, *, args):
    pass


#reading the stored token from config.json
with open("config.json") as file:
    config = json.load(file)

#runs the bot
bot.run(config["TOKEN"])