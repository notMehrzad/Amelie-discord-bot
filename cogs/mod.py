import discord
from discord.ext import commands

class Mod(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name = "mod")
    async def mod(self, ctx: commands.Context[commands.Bot], cmd: str | None, target: discord.Member | None):
        print(cmd, target)
        #if user runs the command in dm
        if not ctx.guild:
            await ctx.reply("You can only do moderation commands in a server.")
            return
        
        #if user didn't enter any subcommand
        if cmd is None:
            await ctx.reply("You must enter a subcommand for this command.")
            return
        
        if not isinstance(type(target), discord.Member):
            await ctx.reply("You must enter a valid member as target.")
            return
        
        #if user didn't enter any target member
        if target is None:
            await ctx.reply("You must enter a target member for this command.")
            return
        
        #if user wants to do moderation command on himself
        if target.id == ctx.author.id:
            await ctx.reply("You can't do moderation commands on yourself.")
            return
        
        #if user wants to do moderation command on the bot
        if target.id == ctx.guild.me.id:
            await ctx.reply("You can't do my moderation commands on myself.\nnice try.")
            return
        
        cmd = cmd.lower()

        #kick subcommand
        if cmd in ["kick", "k"]:
            if not ctx.permissions.kick_members:
                await ctx.reply("You have no permission to *kick* this member.")
                return
            if not ctx.bot_permissions.kick_members:
                await ctx.reply("I have no permisson to *kick* this member.")
                return

        #ban subcommand
        elif cmd in ["ban", "b"]:
            if not ctx.permissions.ban_members:
                await ctx.reply("You have no permission to *ban* this member.")
                return
            if not ctx.bot_permissions.ban_members:
                await ctx.reply("I have no permisson to *ban* this member.")
                return

        #time out subcommand
        elif cmd in ["timeout", "t"]:
            if not ctx.permissions.moderate_members:
                await ctx.reply("You have no permission to *time out* this member.")
                return
            if not ctx.bot_permissions.moderate_members:
                await ctx.reply("I have no permisson to *time out* this member.")
                return
            
            #target.timeout()

        else:
            await ctx.reply("You must enter a valid subcommand.")
            return
        
    @mod.error
    async def mod_error(self, ctx: commands.Context[commands.Bot], error: Exception):
        #if user mentioned an invalid user
        if isinstance(error, commands.MemberNotFound):
            await ctx.reply("Member not found. Please mention a valid user.")
        else:
            print(f"❌ something went wrong with mod command: {error}")
            await ctx.reply("something went wrong with **mod**.")
        


async def setup(bot: commands.Bot):
    await bot.add_cog(Mod(bot))