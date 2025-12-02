import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
from database import connection
from cogs.utility.help import HelpData
from logHandler import loggerSetup

logger = loggerSetup(__name__)

class AnonBlockList(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    Help: HelpData = {
        "help": "",
        "brief": "Shows the anonymous block list of the user.",
        "usage": "",
        "aliases": ["anonbl"],
        "extras": {"Category": "Anonymous", "dm-only": "Yes"}
    }

    @commands.command(
            name = "anonblocklist",
            help = Help["help"],
            brief = Help["brief"],
            usage = Help["usage"],
            aliases = Help["aliases"],
            extras = Help["extras"]
    )
    async def anonblocklist(self, ctx: commands.Context[commands.Bot]):
        #if user runs the command in a server
        if ctx.guild:
            return await ctx.reply("This command can only be used in Amélie's dm.")

        conn = await connection() #makes a connection to the database
        conn.row_factory = aiosqlite.Row

        #checks if the user has a public id
        async with conn.execute("""
        SELECT public_id FROM anonpublicids
        WHERE user_id = ?;
        """, (ctx.author.id,)) as cursor:
            row = await cursor.fetchone()
        if not row:
            return await ctx.reply("You have no public ID which means you have no block list either.")
        
        public_id: str = row["public_id"]

        #fetches all blocked users
        async with conn.execute("""
        SELECT sender_anon_id FROM anonusercontact
        WHERE public_id = ? AND blocked = ?;
        """, (public_id, 1)) as cursor:
            row = await cursor.fetchall()
        #if no user was blocked, notifies the user
        if not row:
            return await ctx.reply("Your block list is empty.")
        
        #sends the result
        resultEmbed = discord.Embed(
            title = "Anonymous Block List",
            description = "\n".join(f"{i}. {v["sender_anon_id"]}" for i, v in enumerate(row, start = 1)),
            color = discord.Color.blurple()
        )
        await ctx.reply(embed = resultEmbed)

    @anonblocklist.error
    async def anonblocklist_error(self, ctx: commands.Context[commands.Bot], error: Exception):
        logger.exception(f"❌ something went wrong with anonblocklist command:")
        await ctx.reply("something went wrong with **anonblocklist**.")

    #anonblocklist slash command
    @app_commands.command(
        name = "anonblocklist",
        description = Help["brief"],
        extras = Help["extras"]
    )
    @app_commands.dm_only()
    async def slashAnonblocklist(self, interaction: discord.Interaction):
        conn = await connection() #makes a connection to the database
        conn.row_factory = aiosqlite.Row

        #checks if the user has a public id
        async with conn.execute("""
        SELECT public_id FROM anonpublicids
        WHERE user_id = ?;
        """, (interaction.user.id,)) as cursor:
            row = await cursor.fetchone()
        if not row:
            return await interaction.response.send_message("You have no public ID which means you have no block list either.", ephemeral = True)
        
        public_id: str = row["public_id"]

        #fetches all blocked users
        async with conn.execute("""
        SELECT sender_anon_id FROM anonusercontact
        WHERE public_id = ? AND blocked = ?;
        """, (public_id, 1)) as cursor:
            row = await cursor.fetchall()
        #if no user was blocked, notifies the user
        if not row:
            return await interaction.response.send_message("Your block list is empty.", ephemeral = True)
        
        #sends the result
        resultEmbed = discord.Embed(
            title = "Anonymous Block List",
            description = "\n".join(f"{i}. {v["sender_anon_id"]}" for i, v in enumerate(row, start = 1)),
            color = discord.Color.blurple()
        )
        await interaction.response.send_message(embed = resultEmbed)

    @slashAnonblocklist.error
    async def slashAnonblocklist_error(self, interaction: discord.Interaction, error: Exception):
        logger.exception(f"❌ something went wrong with /anonblocklist command:")
        try:
            await interaction.response.send_message("something went wrong with **anonblocklist**.", ephemeral = True)
        except discord.InteractionResponded:
            await interaction.followup.send("something went wrong with **anonblocklist**.", ephemeral = True)


async def setup(bot: commands.Bot):
    await bot.add_cog(AnonBlockList(bot))