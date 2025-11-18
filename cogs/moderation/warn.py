import discord
from discord.ext import commands
import sys
import os

parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent)

from database import connection

class Warn(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
            name = "warn",
            aliases = ["w"],
            usage = "<target (mention *or* id)> <reason[*optional*]>",
            brief = "Warns a member from the server.",
            help = (
                ""
            ),
            extras = {"Category": "Moderation", "Permissions needed": "`Kick, Approve and Reject Members`", "in-Server": "Yes"}
    )
    async def warn(self, ctx: commands.Context[commands.Bot], user: discord.User | int | str | None = None, *, reason: str | None = None):
        if not ctx.guild or not isinstance(ctx.author, discord.Member):
            return await ctx.reply("You can only run moderation commands in a server.")
        
        #if the user has no permission to warn
        if not ctx.author.guild_permissions.kick_members:
            return await ctx.reply("You have no permission to *warn* Members.")
        
        #if the bot has no permission to warn
        if not ctx.guild.me.guild_permissions.kick_members:
            return await ctx.reply("I have no permisson to *warn* Members.")
        
        #if user didn't enter any target member
        if not user:
            return await ctx.reply("You must mention a target Member for this command.")
        
        #if user mentions an invalid user
        if not isinstance(user, (discord.abc.User, int)):
            raise commands.BadArgument
        
        try:
            user = (self.bot.get_user(user) or await self.bot.fetch_user(user)) if isinstance(user, int) else user #trys to fetch the target if id is given
        except discord.NotFound:
            return await ctx.reply(f"User with given ID doesn't exist.")
        
        target = ctx.guild.get_member(user.id) #fetches the target user from the server, None if not found
        if not target:
            return await ctx.reply(f"{user.display_name} is not a Member of this server.")
        
        #if user wants to warn himself
        if target.id == ctx.author.id:
            return await ctx.reply("You can't warn yourself!")
        
        #if user wants to warn the server owner
        if target.id == ctx.guild.owner_id:
            return await ctx.reply("You can't warn the server *Owner*.")
        
        #if user wants to run moderation command on the bot
        if target.id == ctx.me.id:
            return await ctx.reply("You can't run my moderation commands on myself darling.")
        
        #if user wants to warn bots
        if target.bot:
            return await ctx.reply("-agh seriously?. You can't warn bots.")
        
        #if user has lower or equal role position than target
        if target.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.reply("You can't warn a Member with *higher or equal* role position as you.")
        
        #if the bot has lower or equal role position than target
        if target.top_role >= ctx.guild.me.top_role:
            return await ctx.reply("I can't warn a Member with *higher or equal* role position as me.")
        
        #warns the target
        warnLimit = 3 #allowed number of warnings before getting kicked

        #warns the target
        conn = await connection() #makes a connection to the database

        #creates the warn ID based on the last warn id
        async with conn.execute("""
        SELECT COALESCE(MAX(user_warn_id), 0) + 1
        FROM warns
        WHERE server_id = ? AND user_id = ?;
        """, (ctx.guild.id, target.id)) as cursor:
            result = await cursor.fetchone()
        warnID: int = result[0] if result else 1
            
        #inserts a new warn for given target
        await conn.execute("""
        INSERT INTO warns (server_id, user_warn_id, mod_id, user_id, reason, timestamp)
        VALUES (?, ?, ?, ?, ?, ?);
        """, (ctx.guild.id, warnID, ctx.author.id, target.id, reason, discord.utils.utcnow()))
        await conn.commit() #commits and saves the changes

        #counts the number of warns the target has
        async with conn.execute("""
        SELECT COUNT(*) FROM warns
        WHERE server_id = ? AND user_id = ?;
        """, (ctx.guild.id, target.id)) as cursor:
            result = await cursor.fetchone()
        warnCount: int = result[0] if result else 0

        await conn.close()

        await ctx.reply(f"{target.mention} has been warned." + (f"\nreason: {reason}" if reason else ""))

        #if the target has over alowed number of warns, kicks it
        if warnCount >= warnLimit:
            try:
                #await ctx.guild.kick(user = target, reason = f"Reached the maximum allowed number of warnings *({warnLimit})*.")
                await ctx.reply(f"{target.display_name} has been kicked due to reaching the maximum allowed number of warnings *({warnLimit})*.")
            except Exception as e:
                print(f".kick failed to kick: {e}")
                await ctx.reply("Failed to kick.")
        
    @warn.error
    async def warn_error(self, ctx: commands.Context[commands.Bot], error: commands.CommandError):
        #if user entered an invalid user
        if isinstance(error, commands.BadArgument):
            await ctx.reply("Member not found. Please mention a valid member.")
        else:
            print(f"❌ something went wrong with warn command: {error}")
            await ctx.reply("something went wrong with **warn**.")

        
async def setup(bot: commands.Bot):
    await bot.add_cog(Warn(bot))