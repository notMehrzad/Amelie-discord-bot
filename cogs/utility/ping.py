import discord
from discord.ext import commands
from discord import app_commands
import time
import asyncio
from logHandler import loggerSetup

logger = loggerSetup(__name__)

class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
            name = "ping",
            brief = "Pings Amélie.",
            help = (
                "Checks Amelies conenction speed by measuring WebSocket Latency (which is the delay between bots server and Discord Gateway) and Bot Latency"
                " (which is the time it takes Amelie to send a message and recieve a response)."
            ),
            extras = {"Category": "Utility"}
    )
    async def ping(self, ctx: commands.Context[commands.Bot]):
        pings: list[float] | None = [] #stores pings results
        pingNumbers = 4

        msg = await ctx.reply("pinging...") #initial message

        ws = self.bot.latency * 1000 #getting websocket latency
        #starts pinging n times
        for i in range(pingNumbers):
            
            try:
                start = time.perf_counter()
                await msg.edit(content = f"ping {i + 1}..")
                end = time.perf_counter()
            #if user deletes the pings message
            except discord.NotFound:
                pings = None
                break
            
            msg_latency = (end - start) * 1000
            pings.append(msg_latency) #stores the nth ping in a list
            await asyncio.sleep(0.1)
        if pings:
            avg = round(sum(pings) / pingNumbers, 2) #getting REST latency
            minping = round(min(pings), 2)
            maxping = round(max(pings), 2)
        else:
            avg = minping = maxping = None

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
                + (f"🌐 REST: `{avg:.2f} ms`\n\n" if avg else f"🌐 REST: Failed")
                + (f"Min: `{minping:.2f} ms` | Max: `{maxping:.2f} ms`" if pings else "")
            ),
            timestamp = discord.utils.utcnow()
        ).set_footer(text = f"requested by {ctx.author.name}")
        try:
            await msg.edit(content = None, embed = resultEmbed) #sends the final results
        #if user deletes the pings message
        except discord.NotFound:
            try:
                await ctx.reply(content = None, embed = resultEmbed)
            except discord.NotFound:
                await ctx.send(content = None, embed = resultEmbed)
        

    @ping.error
    async def ping_error(self, ctx: commands.Context[commands.Bot], error: Exception):
        logger.error(f"❌ something went wrong with ping command:", exc_info = error)
        await ctx.reply("something went wrong with **ping**.")

    #ping slash command
    @app_commands.command(
            name = "ping",
            description = "Pings Amélie.",
            extras = {"Category": "Utility"}
    )
    async def slashPing(self, interaction: discord.Interaction):
        pings: list[float] | None = [] #stores pings results
        pingNumbers = 4

        await interaction.response.send_message("pinging...") #initial message

        ws = self.bot.latency * 1000 #getting websocket latency
        #starts pinging n times
        for i in range(pingNumbers):
            
            try:
                start = time.perf_counter()
                await interaction.edit_original_response(content = f"ping {i + 1}..")
                end = time.perf_counter()
            #if user deletes the pings message
            except discord.NotFound:
                pings = None
                break
            
            msg_latency = (end - start) * 1000
            pings.append(msg_latency) #stores the nth ping in a list
            await asyncio.sleep(0.1)
        if pings:
            avg = round(sum(pings) / pingNumbers, 2) #getting REST latency
            minping = round(min(pings), 2)
            maxping = round(max(pings), 2)
        else:
            avg = minping = maxping = None

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
                + (f"🌐 REST: `{avg:.2f} ms`\n\n" if avg else f"🌐 REST: Failed")
                + (f"Min: `{minping:.2f} ms` | Max: `{maxping:.2f} ms`" if pings else "")
            ),
            timestamp = discord.utils.utcnow()
        ).set_footer(text = f"requested by {interaction.user.name}")
        try:
            await interaction.edit_original_response(content = None, embed = resultEmbed) #sends the final results
        #if user deletes the pings message
        except discord.NotFound:
            await interaction.followup.send(embed = resultEmbed)

    @slashPing.error
    async def slashPing_error(self, interaction: discord.Interaction, error: Exception):
        logger.exception(f"❌ something went wrong with /Ping command:")
        await interaction.followup.send("something went wrong with **ping**.", ephemeral = True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Ping(bot))
