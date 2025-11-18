from discord.ext import commands
import json

with open("config.json") as file:
    config = json.load(file)

class StartUp(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    #command cog
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
    async def cog(self, ctx: commands.Context[commands.Bot], cmd: str | None = None, extension: str | None = None):
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

        #reload subcommand
        if cmd in ["reload", "r"]:
            #reloads all cogs if no extension is given
            if not extension or extension == "all":
                msg = await ctx.reply("Reloading all cogs..")

                print("\n--------------")
                for ext in list(self.bot.extensions):
                    await self.bot.reload_extension(ext)
                    print(f"🔄️ {ext.removeprefix("cogs.")} cog is reloaded.")
                
                await msg.edit(content = "All cogs have been reloaded succesfully. ✅", delete_after = 5)
            
            elif "cogs." + extension not in self.bot.extensions:
                await ctx.reply(f"`{extension}` is not a loaded cog.", delete_after = 5)
                await ctx.message.delete(delay = 5)
                return

            #reloads the given extension (if any)
            else:
                msg = await ctx.reply(f"Reloading `{extension}` cog..")

                print("\n--------------")
                await self.bot.reload_extension(f"cogs.{extension}")

                print(f"🔄️ {extension.removeprefix("cogs.")} cog is reloaded.")
                await msg.edit(content = f"`{extension}` cog has been reloaded succesfully. ✅", delete_after = 5)

            await ctx.message.delete()
        
        #if the subcommand is list
        elif cmd in ["list", "show"]:
            extensionlist = list(self.bot.extensions)
            print(f"\n--------------\n{extensionlist}")
            await ctx.reply(content = "Cogs list has been sent. ✅", delete_after = 5)
            await ctx.message.delete(delay = 5)

        #if user entered unvalid subcommand
        else:
            await ctx.reply(content = "Enter a valid subcommand.", delete_after = 5)
            await ctx.message.delete(delay = 5)

    @cog.error
    async def cog_error(self, ctx: commands.Context[commands.Bot], error: Exception):
        print(f"❌ something went wrong with cog command: {error}")
        await ctx.reply("something went wrong with **cog**.", delete_after = 5)


async def setup(bot: commands.Bot):
    await bot.add_cog(StartUp(bot))