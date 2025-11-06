import discord
from discord.ext import commands
from datetime import timedelta, timezone
import dateparser
import re

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
        
    #kick subcommand
    @commands.command(name = "kick", aliases = ["k"])
    async def kick(self, ctx: commands.Context[commands.Bot], target: discord.Member | None = None, *, reason: str | None = None):
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
        if not target:
            return await ctx.reply("You must mention a target Member for this command.")
        
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
        except Exception:
            await ctx.reply("Failed to kick.")

    @kick.error
    async def kick_error(self, ctx: commands.Context[commands.Bot], error: commands.CommandError):
        #if user entered an invalid user
        if isinstance(error, commands.BadArgument):
            await ctx.reply("Member not found. Please mention a valid user.")
        else:
            print(f"❌ something went wrong with mod-kick command: {error}")
            await ctx.reply("something went wrong with **kick**.")

    #ban subcommand
    @commands.command(name = "ban", aliases = ["b"])
    async def ban(self, ctx: commands.Context[commands.Bot], target: discord.User | None = None, *, reason: str | None = None):
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
        if not target:
            return await ctx.reply("You must mention a target Member for this command.")
        
        #checks if the entered target is a member of the server
        if not isinstance(target, discord.Member):
            #if the target is not a member and is in the ban list
            try:
                await ctx.guild.fetch_ban(discord.Object(id = target.id))
                await ctx.reply(f"{target.display_name} is banned already.")
                return
            except discord.NotFound:
                return await ctx.reply(f"{target.display_name} is not a member of this server.")
        
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
        except Exception:
            await ctx.reply("Failed to ban.")

    @ban.error
    async def ban_error(self, ctx: commands.Context[commands.Bot], error: commands.CommandError):
        #if user entered an invalid user
        if isinstance(error, commands.BadArgument):
            await ctx.reply("Member not found. Please mention a valid user.")
        else:
            print(f"❌ something went wrong with mod-ban command: {error}")
            await ctx.reply("something went wrong with **ban**.")

    #timeout command
    @commands.command(name = "timeout", aliases = ["to"])
    async def timeout(self, ctx: commands.Context[commands.Bot], target: discord.User | None = None, untilStr: str | None = None, *, reason: str | None = None):
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
        if not target:
            return await ctx.reply("You must mention a target Member for this command.")
        
        targetMember = ctx.guild.get_member(target.id) #fetchs the target user from server
        #if the mentioned user is not a member of the server
        if not targetMember:
            return await ctx.reply(f"{target.display_name} is not a Member of this server.")
        
        #if user trys to time out itself
        if targetMember.id == ctx.author.id:
            return await ctx.reply("You can't time out yourself.")
        
        #if user trys to time out the server owner
        if targetMember.id == ctx.guild.owner_id:
            return await ctx.reply("You can't time out the server *Owner*.")
        
        #if user trys to time out a bot except the bot
        if targetMember.bot and targetMember.id != ctx.me.id:
            return await ctx.reply("You can't time out poor bots.")
        
        #if user trys to time out the bot itself
        if targetMember.id == ctx.me.id:
            return await ctx.reply("You can't time out me hon.")
        
        #if user has lower or equal role position than target
        if targetMember.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.reply("You can't time out a Member with *higher or equal* role position as you.")
        
        #if the bot has lower or equal role position than target
        if targetMember.top_role >= ctx.guild.me.top_role:
            return await ctx.reply("I can't time out a Member with *higher or equal* role position as me.")
        
        if not untilStr:
            return await ctx.reply("You must specify a time or date, so this Member will be timed out until then. or *false*/*0* to remove the timeout.")
        
        if targetMember.is_timed_out() and untilStr.lower() not in ["false", "0", "remove"]:
            return await ctx.reply(f"{targetMember.display_name} is timed out already.")
        
        #if entered time was 0, removes the timeout
        if untilStr.lower() in ["false", "0", "remove"]:
            if targetMember.is_timed_out():
                await targetMember.timeout(None, reason = reason)
                await ctx.reply(f"{targetMember.display_name}'s timeout has been *removed* via {ctx.author.display_name}." + (f"\nreason: {reason}" if reason else ""))
            else:
                await ctx.reply(f"{targetMember.display_name} has not been timed out at the first place.")
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
            await targetMember.timeout(untilDt, reason = reason)

            if isinstance(until, timedelta):
                await ctx.reply(f"{targetMember.display_name} has been *timed out* via {ctx.author.display_name} for `{until}`." + (f"\nreason: {reason}" if reason else ""))
            else:
                await ctx.reply(f"{targetMember.display_name} has been *timed out* via {ctx.author.display_name} until `{until}` ." + (f"\nreason: {reason}" if reason else ""))

        except Exception:
            await ctx.reply("Failed to time out.")
        
    @timeout.error
    async def timeout_error(self, ctx: commands.Context[commands.Bot], error: commands.CommandError):
        #if user entered an invalid user
        if isinstance(error, commands.BadArgument):
            await ctx.reply("Member not found. Please mention a valid user.")
        else:
            print(f"❌ something went wrong with mod-timeout command: {error}")
            await ctx.reply("something went wrong with **timeout**.")

    @commands.command(name = "unban", aliases = ["ub"])
    async def unban(self, ctx: commands.Context[commands.Bot], targetId: int | None = None, *, reason: str = "`no reason provided`"):
        #if user runs the command in dm
        if not ctx.guild or not isinstance(ctx.author, discord.Member):
            return await ctx.reply("You can only run moderation commands in a server.")
        
        #if the user has no permission to unban
        if not ctx.author.guild_permissions.ban_members:
            return await ctx.reply("You have no permission to *unban* Members.")
        
        #if the bot has no permission to unban
        if not ctx.guild.me.guild_permissions.ban_members:
            return await ctx.reply("I have no permisson to *unban* Members.")
        
        #if user didn't enter any target member
        if not targetId:
            return await ctx.reply("You must enter a target user ID for this command.")
        
        #if user wants to unban himself
        if targetId == ctx.author.id:
            return await ctx.reply("You were never banned for you to undo it now.")
        
        #if user wants to do moderation command on the bot
        if targetId == ctx.me.id:
            return await ctx.reply("I was never (and can't be) banned for you to undo it now.")
        
        #if user trys to kick the server owner
        if targetId == ctx.guild.owner_id:
            return await ctx.reply("The server *Owner* was never (and couldn't be) banned for you to undo it now.")
        
        target = await self.bot.fetch_user(targetId) #fetches the user from id
        #unbans the target
        try:
            entry = await ctx.guild.fetch_ban(discord.Object(id = targetId)) #checks if the target is banned
            await ctx.guild.unban(user = entry.user, reason = reason)
            await ctx.reply(f"{target.display_name} has been *unbanned* via {ctx.author.display_name}." + (f"\nreason: {reason}" if reason else ""))
        except discord.NotFound:
            return await ctx.reply(f"{target.display_name} was never banned for you to undo it now.")
    
    @unban.error
    async def unban_error(self, ctx: commands.Context[commands.Bot], error: commands.CommandError):
        #if user entered an invalid user
        if isinstance(error, commands.BadArgument):
            await ctx.reply("Member not found. Please enter a valid user ID.")
        else:
            print(f"❌ something went wrong with mod-unban command: {error}")
            await ctx.reply("something went wrong with **unban**.")

    #سکوت 60
    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return
        
        content = msg.content.strip().split()
        if content[0] != "سکوت":
            return
        
        if not msg.guild or not isinstance(msg.author, discord.Member):
            return await msg.reply("You can only run moderation commands in a server.")
        
        if not msg.author.guild_permissions.moderate_members:
            return await msg.reply("You have no permission to *time out* Members.")
        
        if not msg.guild.me.guild_permissions.moderate_members:
            return await msg.reply("I have no permission to *time out* Members.")
        
        if not msg.reference or not msg.reference.message_id:
            return
        
        try:
            refMsg = await msg.channel.fetch_message(msg.reference.message_id)
            target = msg.guild.get_member(refMsg.author.id)
        except discord.NotFound:
            return
        
        if not target:
            return await msg.reply(f"{refMsg.author.display_name} is not a Member of this server.")
        
        if target.id == msg.author.id:
            return await msg.reply("You can't time out yourself.")
        
        if target.id == msg.guild.owner_id:
            return await msg.reply("You can't time out the server *owner*.")
        
        if target.bot and target.id != msg.guild.me.id:
            return await msg.reply("You can't time out poor bots.")
        
        if target.id == msg.guild.me.id:
            return await msg.reply("You can't time out me hon.")
        
        if target.top_role >= msg.author.top_role:
            return await msg.reply("You can't time out a Member with *higher or equal* role position as you.")
        
        if target.top_role >= msg.guild.me.top_role:
            return await msg.reply("I can't time out a Member with *higher or equal* role position as me.")
        
        if len(content) < 2:
            return await msg.reply("You must specify a time or date, so this Member will be timed out until then. or *false*/*0* to remove the timeout.")
        
        if target.is_timed_out() and content[1].lower() != "0":
            return await msg.reply(f"{target.display_name} is timed out already.")
        
        reason = " ".join(content[2:]) if len(content) > 2 else None
        
        if content[1] == "0":
            if target.is_timed_out():
                await target.timeout(None, reason = reason)
                await msg.reply(f"\u202bسکوت {target.display_name} برداشته شد.\u202c" + (f"\n\u202bcدلیل: {reason}\u202c" if reason else ""))
            else:
                await msg.reply(f"\u202b{target.display_name} از اولش هم ساکت نبوده.\u202c")
            return
        else:
            until = timeDeltaParser(content[1]) or dateparser.parse(content[1])
        
        if not until:
            return await msg.reply("Enter a valid time or date.")
        
        #if the user didn't enter a time between the supported times
        now = discord.utils.utcnow()
        untilDt = now + until if isinstance(until, timedelta) else until
        untilDt = untilDt.replace(tzinfo = timezone.utc)
        if not (now + timedelta(days = 28) >= untilDt >= now + timedelta(minutes = 1)):
            return await msg.reply("Timeout must be at least *60 seconds* or *28 days* at most.")
        
        try:
            await target.timeout(untilDt, reason = reason)
            if isinstance(until, timedelta):
                await msg.reply(f"\u202b{target.display_name} به مدت *{until.total_seconds() / 60}* دقیقه ساکت شد.\u202c" + (f"\n\u202bدلیل: {reason}\u202c" if reason else ""))
            else:
                await msg.reply(f"\u202b{target.display_name} تا *{until}* ساکت شد.\u202c" + (f"\n\u202bدلیل: {reason}\u202c" if reason else ""))
        except Exception:
            await msg.reply("Failed to time out.")

        await self.bot.process_commands(msg)


async def setup(bot: commands.Bot):
    await bot.add_cog(Mod(bot))