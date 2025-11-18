import discord
from discord.ext import commands

class Kick(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
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


async def setup(bot: commands.Bot):
    await bot.add_cog(Kick(bot))