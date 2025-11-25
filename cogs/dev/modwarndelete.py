import discord
from discord.ext import commands
import json
from database import connection
from cogs.utility.help import HelpData
from logHandler import loggerSetup

logger = loggerSetup(__name__)

with open("config.json") as file:
    config = json.load(file)

class ModWarnDelete(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    Help: HelpData = {
        "help": (
            "This command helps moderating the warns table in database."
            "\nIt has three subcommand (all, server, user):"
            "\n-If \"all\" subcommand is used, deletes all warns table data.."
            "\n-If \"server\" subcommand is used, it takes another parameter <id> to fetch the target Server and deletes that server warns table data."
            "\n-If \"user\" subcommand is used, it takes another parameter <id> to fetch the target User and deletes that User warns table data."
        ),
        "brief": "A developer command to moderate warns table from database.",
        "usage": "<subcommand> <id>",
        "aliases": [],
        "extras": {"Category": "Dev", "Subcommands": "all | server | user"}
    }

    @commands.command(
            name = "modwarndelete",
            help = Help["help"],
            brief = Help["brief"],
            usage = Help["usage"],
            aliases = Help["aliases"],
            hidden = True,
            extras = Help["extras"]
    )
    async def modwarndelete(self, ctx:commands.Context[commands.Bot], cmd : str | None = None, id: int | str | None = None):
        #checks if the user is an admin to use the command
        if str(ctx.author.id) not in config["ADMINS"]:
            await ctx.reply(content ="You can't use this command.", delete_after = 5)
            await ctx.message.delete(delay = 5)
            return
        
        #if user doesn't enter a subcommand
        if not cmd:
            await ctx.reply("You must enter a subcommand for this command.", delete_after = 5)
            await ctx.message.delete(delay = 5)
            return
        
        cmd = cmd.lower()

        #deletes all warns table data
        if cmd == "all":
            conn = await connection() #makes a connection to the database

            await conn.execute("DELETE FROM warns;")
            await conn.execute("DELETE FROM sqlite_sequence WHERE name='warns';")
            await conn.commit()
            await conn.close()

            await ctx.reply("All warnings have been cleared.", delete_after = 5)
            await ctx.message.delete(delay = 5)

        #deletes all warns data from a server
        elif cmd == "server":
            if not id:
                await ctx.reply("You must enter a target server ID for this subcommand.", delete_after = 5)
                await ctx.message.delete(delay = 5)
                return
            
            if not isinstance(id, int):
                await ctx.reply("Enter a valid server ID.", delete_after = 5)
                await ctx.message.delete(delay = 5)
                return
            
            try:
                server = self.bot.get_guild(id) or await self.bot.fetch_guild(id)
            except discord.NotFound:
                await ctx.reply("Server with given ID doesn't exist.", delete_after = 5)
                await ctx.message.delete(delay = 5)
                return
            except discord.HTTPException:
                await ctx.reply("Enter a valid server ID.", delete_after = 5)
                await ctx.message.delete(delay = 5)
                return
            
            conn = await connection() #makes a connection to the database

            await conn.execute("""
            DELETE FROM warns
            WHERE server_id = ?
            """, (server.id,))
            await conn.commit()
            await conn.close()

            await ctx.reply(f"All warnings from {server.name} have been cleared.", delete_after = 5)
            await ctx.message.delete(delay = 5)
        
        #deletes all warns data from a user
        elif cmd == "user":
            if not id:
                await ctx.reply("You must enter a target user ID for this subcommand.", delete_after = 5)
                await ctx.message.delete(delay = 5)
                return
            
            if not isinstance(id, int):
                await ctx.reply("Enter a valid user ID.", delete_after = 5)
                await ctx.message.delete(delay = 5)
                return
            
            try:
                target = self.bot.get_user(id) or await self.bot.fetch_user(id)
            except discord.NotFound:
                await ctx.reply("User with given ID doesn't exist.", delete_after = 5)
                await ctx.message.delete(delay = 5)
                return
            except discord.HTTPException:
                await ctx.reply("Enter a valid User ID.", delete_after = 5)
                await ctx.message.delete(delay = 5)
                return
            
            conn = await connection()#makes a connection to the database

            await conn.execute("""
            DELETE FROM warns
            WHERE user_id = ?
            """, (target.id,))
            await conn.commit()
            await conn.close()

            await ctx.reply(f"All warnings from {target.display_name} have been cleared.", delete_after = 5)
            await ctx.message.delete(delay = 5)

        #if entered subcommand is invalid
        else:
            await ctx.reply("Enter a valid subcommand.", delete_after = 5)
            await ctx.message.delete(delay = 5)
            return
        
    @modwarndelete.error
    async def modwarndelete_error(self, ctx: commands.Context[commands.Bot], error: Exception):
        logger.exception(f"❌ something went wrong with modwarndelete command:")
        await ctx.reply("something went wrong with **modwarndelete**.", delete_after = 5)
        

async def setup(bot: commands.Bot):
    await bot.add_cog(ModWarnDelete(bot))