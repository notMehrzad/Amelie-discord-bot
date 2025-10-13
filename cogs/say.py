from discord.ext import commands

class Say(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name = "say", aliases = ["echo"])
    async def say(self, ctx: commands.Context, *, args: str = None):
        if args is None:
            await ctx.reply("you must write the things to be said.")
            return
        
        await ctx.send(args)


async def setup(bot: commands.Bot):
    await bot.add_cog(Say(bot))