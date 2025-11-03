import discord
from discord.ext import commands
from datetime import timedelta
import dateparser
import re

def timeDeltaParser(untilStr: str):
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
    async def kick(self, ctx: commands.Context[commands.Bot], target: discord.Member | None = None, *, reason: str = "`no reason provided`"):
        #if user runs the command in dm
        if not ctx.guild or not isinstance(ctx.author, discord.Member):
            return await ctx.reply("You can only do moderation commands in a server.")
        
        #if the user has no permission to kick
        if not ctx.author.guild_permissions.kick_members:
            return await ctx.reply("You have no permission to *kick* Members.")
        
        #if the bot has no permission to kick
        if not ctx.guild.me.guild_permissions.kick_members:
            return await ctx.reply("I have no permisson to *kick* Members.")
        
        #if user didn't enter any target member
        if not target:
            return await ctx.reply("You must enter a target user for this command.")
        
        #if user wants to kick himself
        if target.id == ctx.author.id:
            return await ctx.reply("You can't kick yourself!")
        
        #if user wants to do moderation command on the bot
        if target.id == ctx.me.id:
            return await ctx.reply("You can't do my moderation commands on myself.\nnice try.")
        
        #if user trys to kick the server owner
        if target.id == ctx.guild.owner_id:
            return await ctx.reply("You can't kick the *Owner*.")
        
        #if user has lower or equal role position than target
        if target.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.reply("You can't kick a Member with *higher or equal* role position as you.")
        
        #if the bot has lower or equal role position than target
        if target.top_role >= ctx.guild.me.top_role:
            return await ctx.reply("I can't kick a Member with *higher or equal* role position as me.")
        
        #kicks the target
        try:
            await target.kick(reason = reason)
            await ctx.reply(f"{target.display_name} has been *kicked* via {ctx.author.display_name}.\nreason: {reason}")
        except discord.Forbidden:
            await ctx.reply("I haven't the proper permission to kick Members.")

    @kick.error
    async def kick_error(self, ctx: commands.Context[commands.Bot], error: commands.CommandError):
        #if user entered an invalid user
        if isinstance(error, commands.BadArgument):
            await ctx.reply("Member not found. Please enter a valid user.")
        else:
            print(f"❌ something went wrong with mod-kick command: {error}")
            await ctx.reply("something went wrong with **kick**.")

    #ban subcommand
    @commands.command(name = "ban", aliases = ["b"])
    async def ban(self, ctx: commands.Context[commands.Bot], target: discord.Member | None = None, *, reason: str | None = None):
        #if user runs the command in dm
        if not ctx.guild or not isinstance(ctx.author, discord.Member):
            return await ctx.reply("You can only do moderation commands in a server.")
        
        #if the user has no permission to ban
        if not ctx.author.guild_permissions.ban_members:
            return await ctx.reply("You have no permission to *ban* Members.")
        
        #if the bot has no permission to ban
        if not ctx.guild.me.guild_permissions.ban_members:
            return await ctx.reply("I have no permisson to *ban* Members.")
        
        #if user didn't enter any target member
        if not target:
            return await ctx.reply("You must enter a target user for this command.")
        
        #if user wants to ban himself
        if target.id == ctx.author.id:
            return await ctx.reply("You can't ban yourself!")
        
        #if user wants to do moderation command on the bot
        if target.id == ctx.me.id:
            return await ctx.reply("You can't do my moderation commands on myself.\nnice try.")
        
        #if user trys to ban the server owner
        if target.id == ctx.guild.owner_id:
            return await ctx.reply("You can't ban the *Owner*.")
        
        #if user has lower or equal role position than target
        if target.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.reply("You can't ban a Member with *higher or equal* role position as you.")
        
        #if the bot has lower or equal role position than target
        if target.top_role >= ctx.guild.me.top_role:
            return await ctx.reply("I can't ban a Member with *higher or equal* role position as me.")
        
        #checks if user is banned already
        try:
            await ctx.guild.fetch_ban(discord.Object(id = target.id))
            await ctx.reply(f"{target.display_name} is banned already.")
            return
        except discord.NotFound:
            pass
        
        #bans the target
        try:
            await ctx.guild.ban(user = target, reason = reason)
            await ctx.reply(f"{target.display_name} has been *banned* via {ctx.author.display_name}.\nreason: {reason}")
        except discord.Forbidden:
            await ctx.reply("I haven't the proper permission to ban Members.")

    @ban.error
    async def ban_error(self, ctx: commands.Context[commands.Bot], error: commands.CommandError):
        #if user entered an invalid user
        if isinstance(error, commands.BadArgument):
            await ctx.reply("Member not found. Please enter a valid user.")
        else:
            print(f"❌ something went wrong with mod-ban command: {error}")
            await ctx.reply("something went wrong with **ban**.")

    #timeout command
    @commands.command(name = "timeout", aliases = ["to"])
    async def timeout(self, ctx: commands.Context[commands.Bot], target: discord.Member | None = None, untilStr: str | None = None, *, reason: str = "`no reason provided`"):
        #if user runs the command in dm
        if not ctx.guild or not isinstance(ctx.author, discord.Member):
            return await ctx.reply("You can only do moderation commands in a server.")
        
        #if the user has no permission to time out
        if not ctx.author.guild_permissions.moderate_members:
            return await ctx.reply("You have no permission to *time out* Members.")
        
        #if the bot has no permission to time out
        if not ctx.guild.me.guild_permissions.moderate_members:
            return await ctx.reply("I have no permisson to *time out* Members.")
        
        #if user didn't enter any target member
        if not target:
            return await ctx.reply("You must enter a target user for this command.")
        
        #if user trys to time out the server owner
        if target.id == ctx.guild.owner_id:
            return await ctx.reply("You can't timeout the server *owner*.")
        
        #if user has lower or equal role position than target
        if target.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.reply("You can't time out a Member with *higher or equal* role position as you.")
        
        #if the bot has lower or equal role position than target
        if target.top_role >= ctx.guild.me.top_role:
            return await ctx.reply("I can't time out a Member with *higher or equal* role position as me.")
        
        if not untilStr:
            return await ctx.reply("You must specify a time so this Member will be timed out until then. or false/0 to remove the timeout.")
        
        #time outs the target
        try:
            until = dateparser.parse(untilStr) or timeDeltaParser(untilStr)

            #if entered until wasn't either a datetime or timedelta
            if not until:
                if untilStr.lower() in ["false", "0", "remove"]:
                    await target.timeout(None, reason = reason)
                    await ctx.reply(f"{target.display_name}'s time out has been *removed* via {ctx.author.display_name}.")
                    return
                else:
                    return await ctx.reply("enter a valid datetime.")
                
            if isinstance(until, timedelta) and not (timedelta(days = 28) >= until >= timedelta(minutes = 2)):
                return await ctx.reply("timeout must be at least *2 minutes* and *28 days* at most.")
            
            if target.is_timed_out():
                return await ctx.reply(f"{target.display_name} is timed out already.")
            
            await target.timeout(until, reason = reason)

            if isinstance(until, timedelta):
                await ctx.reply(f"{target.display_name} has been timed out via {ctx.author.display_name} for `{until}` .\nreason: {reason}")

            else:
                await ctx.reply(f"{target.display_name} has been timed out via {ctx.author.display_name} until `{until}` .\nreason: {reason}")

        except TypeError:
            await ctx.reply("enter a valid datetime.")
        
    @timeout.error
    async def timeout_error(self, ctx: commands.Context[commands.Bot], error: commands.CommandError):
        #if user entered an invalid user
        if isinstance(error, commands.BadArgument):
            await ctx.reply("Member not found. Please enter a valid user.")
        else:
            print(f"❌ something went wrong with mod-timeout command: {error}")
            await ctx.reply("something went wrong with **timeout**.")

    @commands.command(name = "unban", aliases = ["ub"])
    async def unban(self, ctx: commands.Context[commands.Bot], targetId: int | None = None, *, reason: str = "`no reason provided`"):
        #if user runs the command in dm
        if not ctx.guild or not isinstance(ctx.author, discord.Member):
            return await ctx.reply("You can only do moderation commands in a server.")
        
        #if the user has no permission to unban
        if not ctx.author.guild_permissions.ban_members:
            return await ctx.reply("You have no permission to *unban* Members.")
        
        #if the bot has no permission to unban
        if not ctx.guild.me.guild_permissions.ban_members:
            return await ctx.reply("I have no permisson to *unban* Members.")
        
        #if user didn't enter any target member
        if not targetId:
            return await ctx.reply("You must enter a target user for this command.")
        
        #if user wants to unban himself
        if targetId == ctx.author.id:
            return await ctx.reply("You were never banned for you to undo it now.")
        
        #if user wants to do moderation command on the bot
        if targetId == ctx.me.id:
            return await ctx.reply("I was never (and can't be) banned for you to undo it now.")
        
        #if user trys to kick the server owner
        if targetId == ctx.guild.owner_id:
            return await ctx.reply("The server *Owner* was never (and couldn't be) banned for you to undo it now.")
        
        #unbans the target
        target = await self.bot.fetch_user(targetId) #fetches the user from id
        try:
            entry = await ctx.guild.fetch_ban(discord.Object(id = targetId)) #checks if the target is banned
            await ctx.guild.unban(user = entry.user, reason = reason)
            await ctx.reply(f"{target.display_name} has been unbanned via {ctx.author.display_name}.\nreason: {reason}")
        except discord.NotFound:
            return await ctx.reply(f"{target.display_name} was never banned for you to undo it now.")
    
    @unban.error
    async def unban_error(self, ctx: commands.Context[commands.Bot], error: commands.CommandError):
        #if user entered an invalid user
        if isinstance(error, commands.BadArgument):
            await ctx.reply("Member not found. Please enter a valid user.")
        else:
            print(f"❌ something went wrong with mod-unban command: {error}")
            await ctx.reply("something went wrong with **unban**.")

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return
        
        if not msg.guild or not isinstance(msg.author, discord.Member):
            return
        
        if not msg.author.guild_permissions.moderate_members or not msg.guild.me.guild_permissions.moderate_members:
            return
        
        if not msg.reference or not msg.reference.message_id:
            return
        
        try:
            refMsg = await msg.channel.fetch_message(msg.reference.message_id)
        except discord.NotFound:
            return
        
        if not isinstance(refMsg.author, discord.Member):
            return
        
        if refMsg.author.id == msg.guild.owner_id:
            return
        
        if refMsg.author.id == msg.author.id:
            return
        
        if refMsg.author.bot:
            return
        
        if refMsg.author.top_role >= msg.guild.me.top_role or refMsg.author.top_role >= msg.author.top_role:
            return
        
        content = msg.content.strip().split()    
        
        if content[0] != "سکوت":
            return
        
        if len(content) < 2:
            return
        
        try:
            duration = int(content[1])
        except ValueError:
            return
        
        if duration < 1 and duration != 0:
            return
        
        if duration != 0 and refMsg.author.is_timed_out():
            return
        
        try:
            await refMsg.author.timeout(timedelta(minutes = duration) if duration != 0 else None)
            if duration != 0:
                await msg.reply(f"{refMsg.author.display_name} به مدت *{duration}* دقیقه ساکت شد.")
            else:
                await msg.reply(f"سکوت {refMsg.author.display_name} برداشته شد.")
        except Exception:
            return

        await self.bot.process_commands(msg)


async def setup(bot: commands.Bot):
    await bot.add_cog(Mod(bot))