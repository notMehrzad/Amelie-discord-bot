from discord.ext import commands

class StartUp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #print a message when bot is ready
    @commands.Cog.listener()
    async def on_ready(self):
        try:
            print(
                "--------------"
                f"\nWe have logged in as {self.bot.user} ✅"
            )
        except Exception as e:
            print(f"\ncouldn't log in the bot: {e}")

async def setup(bot):
    await bot.add_cog(StartUp(bot))