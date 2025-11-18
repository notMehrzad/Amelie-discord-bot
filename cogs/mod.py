import discord
from discord.ext import commands
from datetime import timedelta, timezone
import dateparser
import re
import aiosqlite
import sys
import os

parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent)

from database import connection

def timeDeltaParser(untilStr: str):
    try:
        return timedelta(minutes = float(untilStr))
    except Exception:
        pass

    pattern = r"(?:(\d+)d)?\s*(?:(\d+)h)?\s*(?:(\d+)m)?\s*(?:(\d+)s)?"
    match = re.fullmatch(pattern, untilStr)

    if not match:
        return None
    
    d, h, m, s = (int(x) if x else 0 for x in match.groups())
    return timedelta(days = d, hours = h, minutes = m, seconds = s)

class Mod(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    #kick command
    @commands.command(
            name = "kick",
            aliases = ["k"],
            usage = "<target> <reason[*optional*]>",
            brief = "Kicks a member from the server.",
            help = (
                ""
            ),
            extras = {"Category": "Moderation", "Permissions needed": "`Kick, Approve and Reject Members`", "in-Server": "Yes"}
    )
    async def kick(self, ctx: commands.Context[commands.Bot], user: discord.User | str | None = None, *, reason: str | None = None):
        #if user runs the command in dm
        if not ctx.guild or not isinstance(ctx.author, discord.Member):
            return await ctx.reply("You can only run moderation commands in a server.")
        
        #if the user has no permission to kick
        if not ctx.author.guild_permissions.kick_members:
            return await ctx.reply("You have no permission to *kick* Members.")
        
        #if the bot has no permission to kick
        if not ctx.guild.me.guild_permissions.kick_members:
            return await ctx.reply("I have no permisson to *kick* Members.")
        
        #if user didn't enter any target member
        if not user:
            return await ctx.reply("You must mention a target Member for this command.")
        
        #if user mentions an invalid user
        if not isinstance(user, discord.abc.User):
            raise commands.BadArgument
        
        target = ctx.guild.get_member(user.id) #fetches the target user from the server, None if not found
        if not target:
            return await ctx.reply(f"{user.display_name} is not a Member of this server.")
        
        #if user wants to kick himself
        if target.id == ctx.author.id:
            return await ctx.reply("You can't kick yourself!")
        
        #if user wants to run moderation command on the bot
        if target.id == ctx.me.id:
            return await ctx.reply("You can't run my moderation commands on myself darling.")
        
        #if user trys to kick the server owner
        if target.id == ctx.guild.owner_id:
            return await ctx.reply("You can't kick the server *Owner*.")
        
        #if user has lower or equal role position than target
        if target.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.reply("You can't kick a Member with *higher or equal* role position as you.")
        
        #if the bot has lower or equal role position than target
        if target.top_role >= ctx.guild.me.top_role:
            return await ctx.reply("I can't kick a Member with *higher or equal* role position as me.")
        
        #kicks the target
        try:
            await ctx.guild.kick(user = target, reason = reason)
            await ctx.reply(f"{target.display_name} has been *kicked* via {ctx.author.display_name}." + (f"\nreason: {reason}" if reason else ""))
        except Exception as e:
            print(f".kick failed to kick: {e}")
            await ctx.reply("Failed to kick.")

    @kick.error
    async def kick_error(self, ctx: commands.Context[commands.Bot], error: commands.CommandError):
        #if user entered an invalid user
        if isinstance(error, commands.BadArgument):
            await ctx.reply("Member not found. Please mention a valid member.")
        else:
            print(f"❌ something went wrong with mod-kick command: {error}")
            await ctx.reply("something went wrong with **kick**.")

    #ban command
    @commands.command(
            name = "ban",
            aliases = ["b"],
            usage = "<target> <reason[*optional*]>",
            brief = "Bans a member from the server.",
            help = (
                ""
            ),
            extras = {"Category": "Moderation", "Permissions needed": "`Ban Members`", "in-Server": "Yes"}
    )
    async def ban(self, ctx: commands.Context[commands.Bot], user: discord.User | str | None = None, *, reason: str | None = None):
        #if user runs the command in dm
        if not ctx.guild or not isinstance(ctx.author, discord.Member):
            return await ctx.reply("You can only run moderation commands in a server.")
        
        #if the user has no permission to ban
        if not ctx.author.guild_permissions.ban_members:
            return await ctx.reply("You have no permission to *ban* Members.")
        
        #if the bot has no permission to ban
        if not ctx.guild.me.guild_permissions.ban_members:
            return await ctx.reply("I have no permisson to *ban* Members.")
        
        #if user didn't enter any target member
        if not user:
            return await ctx.reply("You must mention a target Member for this command.")
        
        #if user mentions an invalid user
        if not isinstance(user, discord.abc.User):
            raise commands.BadArgument
        
        target = ctx.guild.get_member(user.id) #fetches the target user from the server, None if not found
        if not target:
            #if the target is not a member and is in the ban list
            try:
                await ctx.guild.fetch_ban(discord.Object(id = user.id))
                await ctx.reply(f"{user.display_name} is banned already.")
                return
            except discord.NotFound:
                return await ctx.reply(f"{user.display_name} is not a Member of this server.")
        
        #if user wants to ban himself
        if target.id == ctx.author.id:
            return await ctx.reply("You can't ban yourself.")
        
        #if user wants to run moderation command on the bot
        if target.id == ctx.me.id:
            return await ctx.reply("You can't run my moderation commands on myself.\nnice try.")
        
        #if user trys to ban the server owner
        if target.id == ctx.guild.owner_id:
            return await ctx.reply("You can't ban the server *Owner*.")
        
        #if user has lower or equal role position than target
        if target.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.reply("You can't ban a Member with *higher or equal* role position as you.")
        
        #if the bot has lower or equal role position than target
        if target.top_role >= ctx.guild.me.top_role:
            return await ctx.reply("I can't ban a Member with *higher or equal* role position as me.")
        
        #bans the target
        try:
            await ctx.guild.ban(user = target, reason = reason)
            await ctx.reply(f"{target.display_name} has been *banned* via {ctx.author.display_name}." + (f"\nreason: {reason}" if reason else ""))
        except Exception as e:
            print(f".ban failed to ban: {e}")
            await ctx.reply("Failed to ban.")

    @ban.error
    async def ban_error(self, ctx: commands.Context[commands.Bot], error: commands.CommandError):
        #if user entered an invalid user
        if isinstance(error, commands.BadArgument):
            await ctx.reply("Member not found. Please mention a valid member.")
        else:
            print(f"❌ something went wrong with mod-ban command: {error}")
            await ctx.reply("something went wrong with **ban**.")

    #timeout command
    @commands.command(
            name = "timeout",
            aliases = ["to"],
            usage = "<target> <date *or* time> <reason[*optional*]>",
            brief = "Time outs a member from the server.",
            help = (
                ""
            ),
            extras = {"Category": "Moderation", "Permissions needed": "`Timeout Members`", "in-Server": "Yes"}
    )
    async def timeout(self, ctx: commands.Context[commands.Bot], user: discord.User | str | None = None, untilStr: str | None = None, *, reason: str | None = None):
        #if user runs the command in dm
        if not ctx.guild or not isinstance(ctx.author, discord.Member):
            return await ctx.reply("You can only run moderation commands in a server.")
        
        #if the user has no permission to time out
        if not ctx.author.guild_permissions.moderate_members:
            return await ctx.reply("You have no permission to *time out* Members.")
        
        #if the bot has no permission to time out
        if not ctx.guild.me.guild_permissions.moderate_members:
            return await ctx.reply("I have no permisson to *time out* Members.")
        
        #if user didn't mention any target user
        if not user:
            return await ctx.reply("You must mention a target Member for this command.")
        
        #if user mentions an invalid user
        if not isinstance(user, discord.abc.User):
            raise commands.BadArgument
        
        target = ctx.guild.get_member(user.id) #fetches the target user from the server, None if not found
        if not target:
            return await ctx.reply(f"{user.display_name} is not a Member of this server.")
        
        #if user trys to time out itself
        if target.id == ctx.author.id:
            return await ctx.reply("You can't time out yourself.")
        
        #if user trys to time out the server owner
        if target.id == ctx.guild.owner_id:
            return await ctx.reply("You can't time out the server *Owner*.")
        
        #if user trys to time out the bot itself
        if target.id == ctx.me.id:
            return await ctx.reply("You can't time out me hon.")
        
        #if user trys to time out a bot except the bot
        if target.bot:
            return await ctx.reply("You can't time out poor bots.")
        
        #if user has lower or equal role position than target
        if target.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.reply("You can't time out a Member with *higher or equal* role position as you.")
        
        #if the bot has lower or equal role position than target
        if target.top_role >= ctx.guild.me.top_role:
            return await ctx.reply("I can't time out a Member with *higher or equal* role position as me.")
        
        if not untilStr:
            return await ctx.reply("You must specify a time or date, so this Member will be timed out until then. or *false*/*0* to remove the timeout.")
        
        if target.is_timed_out() and untilStr.lower() not in ["false", "0", "remove"]:
            return await ctx.reply(f"{target.display_name} is timed out already.")
        
        #if entered time was 0, removes the timeout
        if untilStr.lower() in ["false", "0", "remove"]:
            if target.is_timed_out():
                await target.timeout(None, reason = reason)
                await ctx.reply(f"{target.display_name}'s timeout has been *removed* via {ctx.author.display_name}." + (f"\nreason: {reason}" if reason else ""))
            else:
                await ctx.reply(f"{target.display_name} has not been timed out at the first place.")
            return
        else:
            until = timeDeltaParser(untilStr) or dateparser.parse(untilStr)

        #if entered time wasn't either a datetime or timedelta
        if not until:
            return await ctx.reply("Enter a valid time or date.")
        
        #if the user didn't enter a time between the supported times
        now = discord.utils.utcnow()
        untilDt = now + until if isinstance(until, timedelta) else until
        untilDt = untilDt.replace(tzinfo = timezone.utc)
        if not (now + timedelta(days = 28)) >= untilDt >= now + timedelta(minutes = 1):
            return await ctx.reply("Timeout must be at least *60 seconds* or *28 days* at most.")
            
        #time outs the target
        try:
            await target.timeout(untilDt, reason = reason)

            if isinstance(until, timedelta):
                await ctx.reply(f"{target.display_name} has been *timed out* via {ctx.author.display_name} for `{until}`." + (f"\nreason: {reason}" if reason else ""))
            else:
                await ctx.reply(f"{target.display_name} has been *timed out* via {ctx.author.display_name} until `{until}` ." + (f"\nreason: {reason}" if reason else ""))

        except Exception as e:
            print(f".timeout failed to time out: {e}")
            await ctx.reply("Failed to time out.")
        
    @timeout.error
    async def timeout_error(self, ctx: commands.Context[commands.Bot], error: commands.CommandError):
        #if user entered an invalid user
        if isinstance(error, commands.BadArgument):
            await ctx.reply("Member not found. Please mention a valid member.")
        else:
            print(f"❌ something went wrong with mod-timeout command: {error}")
            await ctx.reply("something went wrong with **timeout**.")

    #unban command
    @commands.command(
            name = "unban",
            aliases = ["ub"],
            usage = "<target_ID> <reason[*optional*]>",
            brief = "Unbans a user from the server.",
            help = (
                ""
            ),
            extras = {"Category": "Moderation", "Permissions needed": "`Ban Members`", "in-Server": "Yes"}
    )
    async def unban(self, ctx: commands.Context[commands.Bot], userId: int | str | None = None, *, reason: str = "`no reason provided`"):
        #if user runs the command in dm
        if not ctx.guild or not isinstance(ctx.author, discord.Member):
            return await ctx.reply("You can only run moderation commands in a server.")
        
        #if the user has no permission to unban
        if not ctx.author.guild_permissions.ban_members:
            return await ctx.reply("You have no permission to *unban* Members.")
        
        #if the bot has no permission to unban
        if not ctx.guild.me.guild_permissions.ban_members:
            return await ctx.reply("I have no permisson to *unban* Members.")
        
        #if user doesn't enter any target ID
        if not userId:
            return await ctx.reply("You must enter a target user ID for this command.")
        
        #if user enters an invalid argument
        if not isinstance(userId, int):
            return await ctx.reply("You must enter a valid target user ID.")
        
        try:
            target = self.bot.get_user(userId) or await self.bot.fetch_user(userId) #fetches the user from id
        except discord.NotFound:
            return await ctx.reply(f"User with this ID doesn't exist.")
        
        #if user wants to unban himself
        if target.id == ctx.author.id:
            return await ctx.reply("You were never banned for you to undo it now.")
        
        #if user wants to do moderation command on the bot
        if target.id == ctx.me.id:
            return await ctx.reply("I was never (and can't be) banned for you to undo it now.")
        
        #if user trys to kick the server owner
        if target.id == ctx.guild.owner_id:
            return await ctx.reply("The server *Owner* was never (and couldn't be) banned for you to undo it now.")
        
        #unbans the target
        try:
            entry = await ctx.guild.fetch_ban(discord.Object(id = target.id)) #checks if the target is banned
            await ctx.guild.unban(user = entry.user, reason = reason)
            await ctx.reply(f"{target.display_name} has been *unbanned* via {ctx.author.display_name}." + (f"\nreason: {reason}" if reason else ""))
        except discord.NotFound:
            return await ctx.reply(f"{target.display_name} was never banned for you to undo it now.")
        except Exception as e:
            print(f".unban failed to unban: {e}")
            await ctx.reply("Failed to unban.")
    
    @unban.error
    async def unban_error(self, ctx: commands.Context[commands.Bot], error: commands.CommandError):
        print(f"❌ something went wrong with mod-unban command: {error}")
        await ctx.reply("something went wrong with **unban**.")

    #warn command
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
        
        #if user wants to run moderation command on the bot
        if target.id == ctx.me.id:
            return await ctx.reply("You can't run my moderation commands on myself darling.")
        
        #if user wants to warn bots
        if target.bot:
            return await ctx.reply("-agh seriously?. You can't warn bots.")
        
        #if user wants to warn the server owner
        if target.id == ctx.guild.owner_id:
            return await ctx.reply("You can't warn the server *Owner*.")
        
        #if user has lower or equal role position than target
        if target.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.reply("You can't warn a Member with *higher or equal* role position as you.")
        
        #if the bot has lower or equal role position than target
        if target.top_role >= ctx.guild.me.top_role:
            return await ctx.reply("I can't warn a Member with *higher or equal* role position as me.")
        
        #warns the target
        warnLimit = 3 #allowed number of warnings before getting kicked

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
            print(f"❌ something went wrong with mod-warn command: {error}")
            await ctx.reply("something went wrong with **warn**.")

    #warnlist command
    @commands.command(
            name = "warnlist",
            aliases = ["wl", "warns"],
            usage = "<target (mention *or* ID *or* \"all\")[*optional*]>",
            brief = "Shows warnings of a member from the server.",
            help = (
                ""
            ),
            extras = {"Category": "Moderation", "Permissions needed": "`Kick, Approve and Reject Members`", "in-Server": "Yes"}
    )
    async def warnlist(self, ctx: commands.Context[commands.Bot], user: discord.User | int | str | None = None):
        #if user runs the command in dm
        if not ctx.guild or not isinstance(ctx.author, discord.Member):
            return await ctx.reply("You can only run moderation commands in a server.")
        
        #if the user has no permission to to see the warns
        if not ctx.author.guild_permissions.kick_members:
            return await ctx.reply("You have no permission to *see the warnings* of Members.")
        
        #if the bot has no permission to see the warns
        if not ctx.guild.me.guild_permissions.kick_members:
            return await ctx.reply("I have no permission to *see the warnings* of Members.")
        
        #if user mentions an invalid user
        if isinstance(user, str) and user.lower() != "all":
            raise commands.BadArgument

        #shows warns of the target user
        if user and not isinstance(user, str):
            try:
                target = (self.bot.get_user(user) or await self.bot.fetch_user(user)) if isinstance(user, int) else user #trys to fetch the target if id is given
            except discord.NotFound:
                return await ctx.reply(f"User with this ID doesn't exist.")
            
            #if user wants to run moderation command on the bot
            if target.id == ctx.me.id:
                return await ctx.reply("I have no warnings for you to see. agh.")
            
            #if user trys to see the server owner warns
            if target.id == ctx.guild.owner_id:
                return await ctx.reply("Server *Owner* has no warning i guess?")
                
            conn = await connection() #creates a connection to the database
            conn.row_factory = aiosqlite.Row

            #searchs database with given arguments
            async with conn.execute(
                "SELECT * FROM warns WHERE server_id = ? AND user_id = ? ORDER BY timestamp;",
                (ctx.guild.id, target.id)
                ) as cursor:
                result = await cursor.fetchall()
            await conn.close()

            warns: list[str] = [] #a list to store warnings
            if result:
                for number, warn in enumerate(result, start = 1):
                    #trys to find moderator name
                    try:
                        moderatorUser = (self.bot.get_user(warn["mod_id"]) or await self.bot.fetch_user(warn["mod_id"])) if warn["mod_id"] else None
                    except Exception:
                        moderatorUser = None
                    moderatorName = moderatorUser.mention if moderatorUser else "*unknown*"
                    desc = f"{number}. Warn ID: {warn['user_warn_id']} | Reason: {warn['reason'] if warn['reason'] else "*no reason provided*"} | Moderator: {moderatorName} | Date: {warn['timestamp']}"
                    warns.append(desc)

            resultEmbed = discord.Embed(
                title = f"{target.display_name}'s warnings",
                description = "\n".join(warns) if warns else f"{target.mention} has no warnings.",
                color = discord.Color.dark_blue()
            )
            await ctx.reply(embed = resultEmbed)
            
        #shows all warn list
        else:
            conn = await connection() #creates a connection to the database
            conn.row_factory = aiosqlite.Row

            #searchs database with given arguments
            async with conn.execute(
                "SELECT * FROM warns WHERE server_id = ? ORDER BY timestamp;",
                (ctx.guild.id,)
                ) as cursor:
                result = await cursor.fetchall()
            await conn.close()

            warns: list[str] = [] #a list to store all server warns
            if result:
                for number, warn in enumerate(result, start = 1):
                    #trys to find the target
                    try:
                        target = self.bot.get_user(warn["user_id"]) or await self.bot.fetch_user(warn["user_id"])
                    except discord.NotFound:
                        #if fetched target user doesn't exist, deletes the warning
                        await conn.execute("DELETE FROM warns WHERE warn_id = ?;", (warn['warn_id'],))
                        await conn.commit()
                        await conn.close()
                        continue

                    #trys to find moderators name
                    try:
                        moderatorUser = (self.bot.get_user(warn["mod_id"]) or await self.bot.fetch_user(warn["mod_id"])) if warn["mod_id"] else None
                    except Exception:
                        moderatorUser = None
                    moderatorName = moderatorUser.mention if moderatorUser else "*unknown*"
                    desc = f"{number}. Warn ID: {warn['user_warn_id']} | User: {target.display_name} | Reason: {warn['reason'] if warn['reason'] else "*no reason provided*"} | Moderator: {moderatorName} | Date: {warn['timestamp']}"
                    warns.append(desc)

            resultEmbed = discord.Embed(
                title = f"{ctx.guild.name}'s warning list",
                description = "\n".join(warns) if warns else f"There is no warning commited yet in this server.",
                color = discord.Color.dark_blue()
            )
            await ctx.reply(embed = resultEmbed)

    @warnlist.error
    async def warnlist_error(self, ctx: commands.Context[commands.Bot], error: commands.CommandError):
        #if user entered an invalid user
        if isinstance(error, commands.BadArgument):
            await ctx.reply("User not found. Please mention a valid user.")
        else:
            print(f"❌ something went wrong with mod-warnlist command: {error}")
            await ctx.reply("something went wrong with **warnlist**.")

    #warnclear command
    @commands.command(
            name = "warnclear",
            aliases = ["wc", "warnremove", "wr"],
            usage = "<target (mention *or* id)> <warn ID (*or* \"all\")[*optional*]> <reason[*optional*]>",
            brief = "Clears warnings of a member from the server.",
            help = (
                ""
            ),
            extras = {"Category": "Moderation", "Permissions needed": "`Kick, Approve and Reject Members`", "in-Server": "Yes"}
    )
    async def warnclear(self, ctx: commands.Context[commands.Bot], user: discord.User | int | str | None = None, warnId: int | str | None = None, *, reason: str | None = None):
        if not ctx.guild or not isinstance(ctx.author, discord.Member):
            return await ctx.reply("You can only run moderation commands in a server.")
        
        #if the user has no permission to clear warns
        if not ctx.author.guild_permissions.kick_members:
            return await ctx.reply("You have no permission to *clear* Members' warnings.")
        
        #if the bot has no permission to clear warns
        if not ctx.guild.me.guild_permissions.kick_members:
            return await ctx.reply("I have no permisson to *clear* Members' warnings.")
        
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
        
        #if user wants to clear its own warns
        if target.id == ctx.author.id:
            return await ctx.reply("You can't clear your own warnings.")
        
        #if user wants to run moderation command on the bot
        if target.id == ctx.me.id:
            return await ctx.reply("I have no warning for you to remove it now??.")
        
        #if user wants to clear warns of bots
        if target.bot:
            return await ctx.reply("Bots have no warning for you to remove it now.")
        
        #if user wants to clear warns of the server owner
        if target.id == ctx.guild.owner_id:
            return await ctx.reply("Server *Owner* has no warning for you to remove it now.")
        
        #if user has lower or equal role position than target
        if target.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.reply("You can't clear warn of a Member with *higher or equal* role position as you.")
        
        #if the bot has lower or equal role position than target
        if target.top_role >= ctx.guild.me.top_role:
            return await ctx.reply("I can't clear warn of a Member with *higher or equal* role position as me.")
        
        #if user doesn't enter a valid warn id
        if isinstance(warnId, str) and warnId.lower() != "all":
            return await ctx.reply("You must enter a valid warn ID (or \"all\"). you can see warn IDs of a user with `warnlist` command.")
        
        conn = await connection() #makes a connection to the database

        #clears the warn with given id
        if warnId and isinstance(warnId, int):
            #trys to find if target user has the warn with given id or not
            async with conn.execute("""
            SELECT * FROM warns
            WHERE server_id = ? AND user_id = ? AND user_warn_id = ?;
            """, (ctx.guild.id, target.id, warnId)) as cursor:
                result = await cursor.fetchone()
            #if no warn with given id is found, notifys the user
            if not result:
                await conn.close()
                return await ctx.reply(f"{target.display_name} has no warning with that ID.")
            
            #deletes the warn with given id
            await conn.execute("""
            DELETE FROM warns
            WHERE server_id = ? AND user_id = ? AND user_warn_id = ?;
            """, (ctx.guild.id, target.id, warnId))
            await conn.commit()
            await conn.close()
        
            await ctx.reply(f"{target.mention}'s warning with ID {warnId} has been cleared." + (f"\nreason: {reason}" if reason else ""))
        
        #clears all warns of the target
        else:
            #trys to find if target user has any warn or not
            async with conn.execute("""
            SELECT * FROM warns
            WHERE server_id = ? AND user_id = ?;
            """, (ctx.guild.id, target.id)) as cursor:
                result = await cursor.fetchall()
            #if the target has no warn, notifys the user
            if not result:
                await conn.close()
                return await ctx.reply(f"{target.display_name} has no warning with that ID.")
            
            #deletes all warns
            await conn.execute("""
            DELETE FROM warns
            WHERE server_id = ? AND user_id = ?;
            """, (ctx.guild.id, target.id))
            await conn.commit()
            await conn.close()
        
            await ctx.reply(f"{target.mention}'s warnings have been cleared." + (f"\nreason: {reason}" if reason else ""))

    @warnclear.error
    async def warnclear_error(self, ctx: commands.Context[commands.Bot], error: commands.CommandError):
        #if user entered an invalid user
        if isinstance(error, commands.BadArgument):
            await ctx.reply("User not found. Please mention a valid user.")
        else:
            print(f"❌ something went wrong with mod-warnclear command: {error}")
            await ctx.reply("something went wrong with **warnclear**.")

    #سکوت 60
    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return
        
        content = msg.content.strip().split()
        if content[0] != "سکوت":
            return
        
        if not msg.guild or not isinstance(msg.author, discord.Member):
            return await msg.reply("افراد رو فقط داخل یک سرور میتونید ساکت کنید.")
        
        if not msg.author.guild_permissions.moderate_members:
            return await msg.reply("شما اجازه *ساکت کردن* کسی را ندارید.")
        
        if not msg.guild.me.guild_permissions.moderate_members:
            return await msg.reply("من اجازه *ساکت کردن* کسی را ندارم.")
        
        if not msg.reference or not msg.reference.message_id:
            return
        
        try:
            refMsg = await msg.channel.fetch_message(msg.reference.message_id)
            target = msg.guild.get_member(refMsg.author.id)
        except discord.NotFound:
            return
        
        if not target:
            return await msg.reply(f"\u202b{refMsg.author.display_name} عضو این سرور نیست.\u202c")
        
        if target.id == msg.author.id:
            return await msg.reply("نمی توانید خود را ساکت کنید.")
        
        if target.id == msg.guild.owner_id:
            return await msg.reply("نمی توانید *صاحب* سرور را ساکت کنید.")
        
        if target.bot and target.id != msg.guild.me.id:
            return await msg.reply("نمی توانید بات های بدبخت بیچاره را ساکت کنید.")
        
        if target.id == msg.guild.me.id:
            return await msg.reply("نمی توانید من را ساکت کنید.")
        
        if target.top_role >= msg.author.top_role:
            return await msg.reply("نمی توانید عضوی با رول *بالاتر یا برابر* از خودتان را ساکت کنید.")
        
        if target.top_role >= msg.guild.me.top_role:
            return await msg.reply("نمی توانم عضوی با رول *بالاتر یا برابر* از خودم را ساکت کنم.")
        
        if len(content) < 2:
            return await msg.reply("\u202bیک زمان یا تاریخ را مشخص کنید تا این عضو تا آن موقع ساکت شود. و یا *false*/*0* برای برداشتن سکوت.\u202c")
        
        if target.is_timed_out() and content[1].lower() != "0":
            return await msg.reply(f"\u202b{target.display_name} در حال حاضر هم ساکت می باشد.\u202c")
        
        reason = " ".join(content[2:]) if len(content) > 2 else None
        
        if content[1] in ["0", "false"]:
            if target.is_timed_out():
                await target.timeout(None, reason = reason)
                await msg.reply(f"\u202bسکوت {target.display_name} برداشته شد.\u202c" + (f"\n\u202bcدلیل: {reason}\u202c" if reason else ""))
            else:
                await msg.reply(f"\u202b{target.display_name} از اول هم ساکت نبوده.\u202c")
            return
        else:
            until = timeDeltaParser(content[1]) or dateparser.parse(content[1])
        
        if not until:
            return await msg.reply("یک زمان یا تاریخ صحیح وارد کنید.")
        
        #if the user didn't enter a time between the supported times
        now = discord.utils.utcnow()
        untilDt = now + until if isinstance(until, timedelta) else until
        untilDt = untilDt.replace(tzinfo = timezone.utc)
        if not (now + timedelta(days = 28) >= untilDt >= now + timedelta(minutes = 1)):
            return await msg.reply("زمان سکوت باید حداقل *60 ثانیه* و حداکثر *28 روز* باشد.")
        
        try:
            await target.timeout(untilDt, reason = reason)
            if isinstance(until, timedelta):
                await msg.reply(f"\u202b{target.display_name} به مدت *{until.total_seconds() / 60}* دقیقه ساکت شد.\u202c" + (f"\n\u202bدلیل: {reason}\u202c" if reason else ""))
            else:
                await msg.reply(f"\u202b{target.display_name} تا *{until}* ساکت شد.\u202c" + (f"\n\u202bدلیل: {reason}\u202c" if reason else ""))
        except Exception as e:
            print(f"سکوت failed to timeout: {e}")
            await msg.reply("ساکت کردن ناموفق بود.")

        await self.bot.process_commands(msg)


async def setup(bot: commands.Bot):
    await bot.add_cog(Mod(bot))