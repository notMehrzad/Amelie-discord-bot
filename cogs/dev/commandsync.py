from discord.ext import commands
import json
from logHandler import loggerSetup

logger = loggerSetup(__name__)

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
    async def commandsync(self, ctx: commands.Context[commands.Bot]):
        #checks if the user is an admin to use the command
        if str(ctx.author.id) not in config["ADMINS"]:
            await ctx.reply(content ="You can't use this command.", delete_after = 5)
            await ctx.message.delete(delay = 5)
            return
        
        syncedCmds = await self.bot.tree.sync()
        syncedCmds = [("/" + cmd.name) for cmd in syncedCmds]
        print("\n--------------")
        print(f"✔️ {syncedCmds} commands have been synced.")
        await ctx.reply("All slash commands are synced.", delete_after = 5)
        await ctx.message.delete(delay = 5)
    
    @commandsync.error
    async def commandsync_error(self, ctx: commands.Context[commands.Bot], error: Exception):
        logger.exception(f"❌ something went wrong with commandsync command:")
        await ctx.reply("something went wrong with **commandsync**.", delete_after = 5)

async def setup(bot: commands.Bot):
    await bot.add_cog(CommandSync(bot))