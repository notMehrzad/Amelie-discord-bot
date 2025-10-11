from discord.ext import commands
import json
import asyncio

with open("config.json") as file:
    config = json.load(file)

class StartUp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #command cog
    @commands.command(name = "cog")
    async def cog(self, ctx, cmd: str = None, extension: str = None):
        try:
            #checks if the user is an admin to use the command
            if str(ctx.author.id) not in config["ADMINS"]:
                msg = await ctx.reply("You can't use this command.")
                await asyncio.sleep(3)
                await msg.delete()
                await ctx.message.delete()
                return
            
            cmd = cmd.lower() if cmd else None
            extension = extension.lower() if extension else None

            #if the subcommand is reload
            if cmd == "reload":
                #reloads all cogs if no extension is given
                if extension in [None, "all"]:
                    msg = await ctx.reply("Reloading all cogs..")

                    print("\n--------------")
                    for ext in list(self.bot.extensions):
                        await self.bot.reload_extension(ext)
                        print(f"🔄️ {ext.removeprefix("cogs.")} cog is reloaded.")
                    
                    await msg.edit(content = "All cogs have been reloaded succesfully. ✅")
                    await asyncio.sleep(3)
                    await msg.delete()

                #reloads the given extension (if any)
                else:
                    msg = await ctx.reply(f"Reloading `{extension}` cog..")

                    print("\n--------------")
                    await self.bot.reload_extension(f"cogs.{extension}")

                    print(f"🔄️ {extension.removeprefix("cogs.")} cog is reloaded.")
                    await msg.edit(content = f"`{extension}` cog has been reloaded succesfully. ✅")
                    await asyncio.sleep(3)
                    await msg.delete()

                await ctx.message.delete()
            
            #if the subcommand is list
            elif cmd in ["list", "show"]:
                extensionlist = list(self.bot.extensions)
                print(f"\n--------------\n{extensionlist}")
                msg = await ctx.reply("Cogs list has been sent. ✅")
                await asyncio.sleep(3)
                await msg.delete()
                await ctx.message.delete()

            #if user entered no subcommand
            elif cmd is None:
                msg = await ctx.reply("You must enter a subcommand for this command.")
                await asyncio.sleep(3)
                await msg.delete()
                await ctx.message.delete()

            #if user entered unvalid subcommand
            else:
                msg = await ctx.reply("Enter a valid subcommand.")
                await asyncio.sleep(3)
                await msg.delete()
                await ctx.message.delete()

        except Exception as e:
            print(f"\n❌ something went wrong with cog command: {e}")
            msg = await ctx.reply(f"❌ something went wrong with **cog**.")
            await asyncio.sleep(3)
            await msg.delete()


async def setup(bot):
    await bot.add_cog(StartUp(bot))