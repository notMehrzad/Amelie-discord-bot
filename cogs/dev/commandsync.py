from discord.ext import commands
import json

with open("config.json") as file:
    config = json.load(file)

class CommandSync(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
            name = "commandsync",
            hidden = True,
            usage = "",
            brief = "A command for syncing bot command tree.",
            help = "",
            extras = {"Category": "Dev"}
    )
    async def cog(self, ctx: commands.Context[commands.Bot]):
        #checks if the user is an admin to use the command
        if str(ctx.author.id) not in config["ADMINS"]:
            await ctx.reply(content ="You can't use this command.", delete_after = 5)
            await ctx.message.delete(delay = 5)
            return
        
        syncedCmds = await self.bot.tree.sync()
        print(syncedCmds)

async def setup(bot: commands.Bot):
    await bot.add_cog(CommandSync(bot))