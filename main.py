import discord
import json

with open("config.json") as file:
    config = json.load(file)

prefix = "!"

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user} ✅')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith(f"{prefix}hello"):
        await message.channel.send("Hello!")

client.run(config["TOKEN"])