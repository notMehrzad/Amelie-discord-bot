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
    
    @commands.command(name = "mod")
    async def mod(self, ctx: commands.Context[commands.Bot], cmd: str | None = None, target: discord.Member | None = None, untilStr: str | None = None, *, reason: str | None = None):
        print(cmd, target)
        #if user runs the command in dm
        if not ctx.guild or not isinstance(ctx.author, discord.Member):
            return await ctx.reply("You can only do moderation commands in a server.")
        
        #if user dosn't enter any subcommand
        if not cmd:
            return await ctx.reply("You must enter a subcommand for this command.")
        
        #if user didn't enter any target member
        if not target:
            return await ctx.reply("You must enter a target user for this command.")
        
        cmd = cmd.lower()
            
        #if user enters an invalid subcommand
        if cmd not in ["kick", "k", "ban", "b", "timeout", "t", "unban", "ub"]:
            return await ctx.reply("You must enter a valid subcommand for this command.")
        
        #if user wants to do moderation command on himself
        if target.id == ctx.author.id:
            return await ctx.reply("You can't do moderation commands on yourself.")
        
        #if user wants to do moderation command on the bot
        if target.id == ctx.me.id:
            return await ctx.reply("You can't do my moderation commands on myself.\nnice try.")
        
        #if user trys to kick the owner
        if target.id == ctx.guild.owner_id:
            return await ctx.reply("You can't do moderation commands on the *Owner*.")
        
        #kick subcommand
        if cmd in ["kick", "k"]:
            #if the user has no permission to kick
            if not ctx.author.guild_permissions.kick_members:
                return await ctx.reply("You have no permission to *kick* Members.")
            
            #if the bot has no permission to kick
            if not ctx.guild.me.guild_permissions.kick_members:
                return await ctx.reply("I have no permisson to *kick* Members.")
            
            #if user has lower or equal role position than target
            if target.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
                return await ctx.reply(f"You can't kick a Member with *higher or equal* role position as you.")
            
            #if the bot has lower or equal role position than target
            if target.top_role >= ctx.guild.me.top_role:
                return await ctx.reply(f"I can't kick a Member with *higher or equal* role position as me.")
            
            #kicks the target
            try:
                await target.kick(reason = reason)
            except discord.Forbidden:
                await ctx.reply("I haven't the proper permission to kick Members.")

        #ban subcommand
        elif cmd in ["ban", "b"]:
            #if the user has no permission to ban
            if not ctx.author.guild_permissions.ban_members:
                return await ctx.reply("You have no permission to *ban* Members.")
            
            #if the bot has no permission to ban
            if not ctx.guild.me.guild_permissions.ban_members:
                return await ctx.reply("I have no permisson to *ban* Members.")
            
            #if user has lower or equal role position than target
            if target.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
                return await ctx.reply(f"You can't ban a Member with *higher or equal* role position as you.")
            
            #if the bot has lower or equal role position than target
            if target.top_role >= ctx.guild.me.top_role:
                return await ctx.reply(f"I can't ban a Member with *higher or equal* role position as me.")
            
            #bans the target
            try:
                await target.ban(reason = reason)
            except discord.Forbidden:
                await ctx.reply("I haven't the proper permission to ban Members.")

        #time out subcommand
        elif cmd in ["timeout", "t"]:
            #if the user has no permission to time out
            if not ctx.author.guild_permissions.moderate_members:
                return await ctx.reply("You have no permission to *time out* Members.")
            
            #if the bot has no permission to time out
            if not ctx.guild.me.guild_permissions.moderate_members:
                return await ctx.reply("I have no permisson to *time out* Members.")
            
            #if user has lower or equal role position than target
            if target.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
                return await ctx.reply(f"You can't time out a Member with *higher or equal* role position as you.")
            
            #if the bot has lower or equal role position than target
            if target.top_role >= ctx.guild.me.top_role:
                return await ctx.reply(f"I can't time out a Member with *higher or equal* role position as me.")
            
            if not untilStr:
                return await ctx.reply("You must specify a time so this Member will be timed out until then. or false/0 to remove the timeout.")
            
            #time outs the target
            try:
                until = dateparser.parse(untilStr) #parses if user enters datetime, None if invalid

                if not until:
                    until = timeDeltaParser(untilStr) #parses if user enters timedelta and it wasn't datetime, None if invalid

                #if entered until wasn't either a datetime or timedelta
                if not until:
                    if untilStr.lower() in ["false", "0", "remove"]:
                        await target.timeout(None, reason = reason)
                        await ctx.reply(f"{target.display_name}'s time out has been *removed* via {ctx.author.display_name}.")
                        return
                    return await ctx.reply("enter a valid datetime.")
                
                await target.timeout(until, reason = reason)
                await ctx.reply(f"{target.display_name} has been timed out via {ctx.author.display_name}" + f" for `{until}` ." if isinstance(until, timedelta) else f" until `{until}` .")

            except TypeError:
                await ctx.reply("enter a valid datetime.")

        elif cmd in ["unban", "ub"]:
            pass
        
    @mod.error
    async def mod_error(self, ctx: commands.Context[commands.Bot], error: commands.CommandError):
        #if user mentioned an invalid user
        if isinstance(error, commands.BadArgument):
            await ctx.reply("Member not found. Please mention a valid user.")
        else:
            print(f"❌ something went wrong with mod command: {error}")
            await ctx.reply("something went wrong with **mod**.")   
    

async def setup(bot: commands.Bot):
    await bot.add_cog(Mod(bot))