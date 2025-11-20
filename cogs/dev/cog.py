from discord.ext import commands
import json
from logHandler import loggerSetup

logger = loggerSetup(__name__)

with open("config.json") as file:
    config = json.load(file)

class StartUp(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
            name = "cog",
            hidden = True,
            usage = "<subcommand> <cog_name[*optional*]>",
            brief = "A cog moderation command made for developers of the bot.",
            help = (
                "A cog handling command made for developers of the bot."
                "\nif \"reload\" subcommand is used, it takes an optional parameter <cog_name> for reloading that specific cog. if not specified, all cogs will be reloaded instead."
                "\nif \"list\" subcommand is used, it prints the cog list into the bots console."
            ),
            extras = {"Category": "Dev", "Subcommands": "\"reload\"[aliases: \"r\"] | \"list\"[aliases: \"show\"]"}
    )
    async def cog(self, ctx: commands.Context[commands.Bot], cmd: str | None, extension: str | None = None):
        #checks if the user is an admin to use the command
        if str(ctx.author.id) not in config["ADMINS"]:
            await ctx.reply(content ="You can't use this command.", delete_after = 5)
            await ctx.message.delete(delay = 5)
            return
        
        #if user entered no subcommand
        if not cmd:
            await ctx.reply(content ="You must enter a subcommand for this command.", delete_after = 5)
            await ctx.message.delete(delay = 5)
            return
        
        cmd = cmd.lower()
        extension = extension.lower() if extension else None

        extensionList = list(self.bot.extensions) #stores all registered extentions

        #reload subcommand
        if cmd in ["reload", "r"]:
            #reloads all cogs if no extension is given
            if not extension or extension == "all":
                msg = await ctx.reply("Reloading all cogs..")
                print("\n--------------")

                for ext in extensionList:
                    await self.bot.reload_extension(ext)
                    print(f"🔄️ {ext.split(".")[-1]} reloaded.")
                
                await msg.edit(content = "All cogs have been reloaded succesfully. ✅", delete_after = 5)

            #reloads the given extention
            else:
                match = None
                #if given extention is found in registered cogs, stops searching
                for ext in extensionList:
                    if ext.split(".")[-1] == extension:
                        match = ext
                        break
                
                #if no match was found, notifys the user
                if not match:
                    await ctx.reply(f"`{extension}` is not a loaded cog.", delete_after = 5)
                    await ctx.message.delete()
                    return
                
                #reloads the matched extention
                msg = await ctx.reply(f"Reloading `{match.split(".")[-1]}` cog..")
                print("\n--------------")

                await self.bot.reload_extension(match)
                print(f"🔄️ {match.split(".")[-1]} cog is reloaded.")

                await msg.edit(content = f"`{match.split(".")[-1]}` cog has been reloaded succesfully. ✅", delete_after = 5)

            await ctx.message.delete()
        
        #list subcommand
        elif cmd in ["list", "show"]:
            print(f"\n--------------\n{extensionList}")
            await ctx.reply(content = "Cogs list has been sent. ✅", delete_after = 5)
            await ctx.message.delete(delay = 5)

        #invalid subcommand
        else:
            await ctx.reply(content = "Enter a valid subcommand.", delete_after = 5)
            await ctx.message.delete(delay = 5)

    @cog.error
    async def cog_error(self, ctx: commands.Context[commands.Bot], error: Exception):
        logger.error(f"❌ something went wrong with cog command:", exc_info = error)
        await ctx.reply("something went wrong with **cog**.", delete_after = 5)


async def setup(bot: commands.Bot):
    await bot.add_cog(StartUp(bot))