from discord.ext import commands
import json
from cogs.utility.help import HelpData
from logHandler import loggerSetup

logger = loggerSetup(__name__)

with open("config.json") as file:
    config = json.load(file)

class StartUp(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    Help: HelpData = {
        "help": (
            "A cog handling command made for developers of the bot."
            "\nif \"reload\" subcommand is used, it takes an optional parameter <cog_name> for reloading that specific cog. if not specified, all cogs will be reloaded instead."
            "\nif \"list\" subcommand is used, it prints the cog list into the bots console."
        ),
        "brief": "A cog moderation command made for developers of the bot.",
        "usage": "<subcommand> <cog_name[*optional*]>",
        "aliases": [],
        "extras": {"Category": "Dev", "Subcommands": "\"reload\"[aliases: \"r\"] | \"list\"[aliases: \"show\"]"}
    }

    @commands.command(
            name = "cog",
            help = Help["help"],
            brief = Help["brief"],
            usage = Help["usage"],
            aliases = Help["aliases"],
            hidden = True,
            extras = Help["extras"]
    )
    async def cog(self, ctx: commands.Context[commands.Bot], cmd: str | None, extension: str | None = None):
        inGuild = True if ctx.guild else False

        #checks if the user is an admin to use the command
        if str(ctx.author.id) not in config["ADMINS"]:
            msg = await ctx.reply(content ="You can't use this command.")
            if inGuild:
                await msg.delete(delay = 5)
                await ctx.message.delete()
            return
        
        #if user entered no subcommand
        if not cmd:
            msg = await ctx.reply(content ="You must enter a subcommand for this command.")
            if inGuild:
                await msg.delete(delay = 5)
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
                
                await msg.edit(content = "All cogs have been reloaded succesfully. ✅")

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
                    msg = await ctx.reply(f"`{extension}` is not a loaded cog.")
                    if inGuild:
                        await msg.delete(delay = 5)
                        await ctx.message.delete(delay = 5)
                    return
                
                #reloads the matched extention
                msg = await ctx.reply(f"Reloading `{match.split(".")[-1]}` cog..")
                print("\n--------------")

                await self.bot.reload_extension(match)
                print(f"🔄️ {match.split(".")[-1]} cog is reloaded.")

                await msg.edit(content = f"`{match.split(".")[-1]}` cog has been reloaded succesfully. ✅")
            
            if inGuild:
                await msg.delete(delay = 5)
                await ctx.message.delete()
        
        #list subcommand
        elif cmd in ["list", "show"]:
            print(f"\n--------------\n{extensionList}")
            msg = await ctx.reply(content = "Cogs list has been sent to the console. ✅")
            if inGuild:
                await msg.delete(delay = 5)
                await ctx.message.delete(delay = 5)

        #invalid subcommand
        else:
            msg = await ctx.reply(content = "Enter a valid subcommand.")
            if inGuild:
                await msg.delete(delay = 5)
                await ctx.message.delete(delay = 5)

    @cog.error
    async def cog_error(self, ctx: commands.Context[commands.Bot], error: Exception):
        logger.exception(f"❌ something went wrong with cog command:")
        await ctx.reply("something went wrong with **cog**.", delete_after = 5)


async def setup(bot: commands.Bot):
    await bot.add_cog(StartUp(bot))