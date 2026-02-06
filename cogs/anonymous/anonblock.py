import discord
from discord.ext import commands
from discord import app_commands
from database import db
from cogs.anonymous.anonsend import privateIdLength
from cogs.utility.help import HelpData
from logHandler import loggerSetup

logger = loggerSetup(__name__)

class AnonBlock(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    Help: HelpData = {
        "help": "",
        "brief": "Blocks an anonymous sender to prevent them from messaging.",
        "usage": "<private ID> <unblock(y/n) [*optional*]>",
        "aliases": ["anonb"],
        "extras": {"Category": "Anonymous", "dm-only": "Yes"}
    }

    @commands.command(
            name = "anonblock",
            help = Help["help"],
            brief = Help["brief"],
            usage = Help["usage"],
            aliases = Help["aliases"],
            extras = Help["extras"]
    )
    async def anonblock(self, ctx: commands.Context[commands.Bot], private_id: str | None, unblock: str | bool | None = False):
        #if user runs the command in a server
        if ctx.guild:
            return await ctx.reply("This command can only be used in Amélie's dm.")

        #checks if the user has a public id
        row = await db.fetchone("""
        SELECT public_id FROM anonpublicids
        WHERE user_id = ?;
        """, (ctx.author.id,))
        if not row:
            return await ctx.reply("You have no public ID so nobody has messaged you to block or unblock now.")
        
        public_id: str = row["public_id"]

        #if user doesn't enter a private id
        if not private_id:
            return await ctx.reply("You must enter the private ID of anonymous sender to block or unblock.")

        #if entered private id is invalid
        if len(private_id) != privateIdLength:
            return await ctx.reply("Enter a valid private ID.")
        
        #checks if the user with given private id exists in user contact
        row = await db.fetchone("""
        SELECT blocked from anonusercontact
        WHERE public_id = ? AND sender_anon_id = ?;
        """, (public_id, private_id))
        if not row:
            return await ctx.reply("No user with given private ID has messaged you ever.")
        
        if isinstance(unblock, str) and unblock.lower() in ["true", "yes", "y"]:
            unblock = True
        elif isinstance(unblock, str) and unblock.lower() in ["false", "no", "n"]:
            unblock = False
        else:
            return await ctx.reply(f"{unblock} is invalid. Choose either *yes* or *no*.")
        
        #if user with given private id is blocked already
        if not unblock and row["blocked"] == 1:
            return await ctx.reply("This anonymous user is Blocked already.")
        
        #if user with given private id is unblocked already
        if unblock and row["blocked"] == 0:
            return await ctx.reply("This anonymous user is Unblocked already.")
        
        #blocks or unblocks the target user
        await db.execute("""
        UPDATE anonusercontact
        SET blocked = ?
        WHERE public_id = ? AND sender_anon_id = ?;
        """, (1 if not unblock else 0, public_id, private_id))

        #sends the result
        resultEmbed = discord.Embed(
            description = f"Anonymous sender with private ID: {private_id} has been {"*Blocked*" if not unblock else "*Unblocked*"}.",
            color = discord.Color.blurple(),
            timestamp = discord.utils.utcnow()
        )
        await ctx.reply(embed = resultEmbed)

    @anonblock.error
    async def anonblocklist_error(self, ctx: commands.Context[commands.Bot], error: Exception):
        logger.exception(f"❌ something went wrong with anonblock command:")
        await ctx.reply("something went wrong with **anonblock**.")

    #anonblock slash command
    @app_commands.command(
        name = "anonblock",
        description = Help["brief"],
        extras = Help["extras"]
    )
    @app_commands.dm_only()
    @app_commands.describe(private_id = "The private ID of anonymous sender to block.", unblock = "Whether you want to block or unblock the user. (default is False=Block)")
    async def slashAnonblock(self, interaction: discord.Interaction, private_id: str, unblock: bool = False):
        #checks if the user has a public id
        row = await db.fetchone("""
        SELECT public_id FROM anonpublicids
        WHERE user_id = ?;
        """, (interaction.user.id,))
        if not row:
            return await interaction.response.send_message("You have no public ID so nobody has messaged you to block or unblock now.")
        
        public_id: str = row["public_id"]

        #if entered private id is invalid
        if len(private_id) != privateIdLength:
            return await interaction.response.send_message("Enter a valid private ID.")
        
        #checks if the user with given private id exists in user contact
        row = await db.fetchone("""
        SELECT blocked from anonusercontact
        WHERE public_id = ? AND sender_anon_id = ?;
        """, (public_id, private_id))
        if not row:
            return await interaction.response.send_message("No user with given private ID has messaged you ever.")
        
        #if user with given private id is blocked already
        if not unblock and row["blocked"] == 1:
            return await interaction.response.send_message("This anonymous user is Blocked already.")
        
        #if user with given private id is unblocked already
        if unblock and row["blocked"] == 0:
            return await interaction.response.send_message("This anonymous user is Unblocked already.")
        
        #blocks or unblocks the target user
        await db.execute("""
        UPDATE anonusercontact
        SET blocked = ?
        WHERE public_id = ? AND sender_anon_id = ?;
        """, (1 if not unblock else 0, public_id, private_id))

        #sends the result
        resultEmbed = discord.Embed(
            description = f"Anonymous sender with private ID: {private_id} has been {"*Blocked*" if not unblock else "*Unblocked*"}.",
            color = discord.Color.blurple(),
            timestamp = discord.utils.utcnow()
        )
        await interaction.response.send_message(embed = resultEmbed)

    @slashAnonblock.error
    async def slashAnonblock_error(self, interaction: discord.Interaction, error: Exception):
        logger.exception(f"❌ something went wrong with /anonblock command:")
        try:
            await interaction.response.send_message("something went wrong with **anonblock**.", ephemeral = True)
        except discord.InteractionResponded:
            await interaction.followup.send("something went wrong with **anonblock**.", ephemeral = True)


async def setup(bot: commands.Bot):
    await bot.add_cog(AnonBlock(bot))