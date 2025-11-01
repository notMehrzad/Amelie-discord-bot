from discord.ext import commands

class Say(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name = "say", aliases = ["echo"])
    async def say(self, ctx: commands.Context[commands.Bot], *, args: str | None = None):
        if not args:
            return await ctx.reply("You must write the things to be said.")
        
        await ctx.send(args)

    @say.error
    async def say_error(self, ctx: commands.Context[commands.Bot], error: Exception):
        print(f"❌ something went wrong with say command: {error}")
        await ctx.reply("something went wrong with **say**.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Say(bot))