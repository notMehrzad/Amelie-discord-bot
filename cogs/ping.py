import discord
from discord.ext import commands
import time
import asyncio

class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name = "ping")
    async def ping(self, ctx: commands.Context[commands.Bot]):
        pings: list[float] = [] #stores pings results
        pingNumbers = 4

        msg = await ctx.reply("pinging...") #initial message

        ws = self.bot.latency * 1000 #getting websocket latency
        #starts pinging n times
        for i in range(pingNumbers):
            start = time.perf_counter()
            await msg.edit(content = f"ping {i + 1}..")
            end = time.perf_counter()
            msg_latency = (end - start) * 1000
            pings.append(msg_latency) #stores the nth ping in a list
            await asyncio.sleep(0.1)
        avg = round(sum(pings) / pingNumbers, 2) #getting REST latency
        minping = round(min(pings), 2)
        maxping = round(max(pings), 2)

        #defining color based on ws ping strength
        if ws <= 100:
            color = discord.Color.from_str("#00ff59") #green
        elif ws <= 200:
            color = discord.Color.from_str("#ffff00") #yellow
        elif ws <= 400:
            color = discord.Color.from_str("#ffab00") #orange
        else:
            color = discord.Color.from_str("#ff3800") #red

        resultEmbed = discord.Embed(
            color = color,
            title = "Pong! 🏓",
            description = (
                f"📡 WebSocket: `{ws:.2f} ms`\n"
                f"🌐 REST: `{avg:.2f} ms`\n\n"
                f"Min: `{minping:.2f} ms` | Max: `{maxping:.2f} ms`"
            ),
            timestamp = discord.utils.utcnow()
        ).set_footer(text = f"requested by {ctx.author.name}")
        await msg.edit(content = None, embed = resultEmbed) #sends the final results

    @ping.error
    async def ping_error(self, ctx: commands.Context[commands.Bot], error: Exception):
        print(f"❌ something went wrong with ping command: {error}")
        await ctx.reply("something went wrong with **ping**.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Ping(bot))
