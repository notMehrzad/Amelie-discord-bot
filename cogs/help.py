import discord
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
            name = "help",
            help = (
                "Shows a brief information about all commands such as their application, usage, necessery permissions (if any) and etc."
                "Enter commands name for getting the full information about that command or nothing to get the list of brief overview."
            ),
            brief = "Shows a brief information about all commands.",
            usage = "<command_name[optional]>",
            extras = {"category": "General"}

    )
    async def help(self, ctx: commands.Context[commands.Bot], cmdStr: str | None = None):
        #help for specific command
        if cmdStr:
            cmd = self.bot.get_command(cmdStr)

            if not cmd:
                return await ctx.reply(f"{cmdStr} doesn't exist. enter a valid command.")
            
            cmdEmbed = discord.Embed(
                title = f"Help: {cmd.name}",
                description = cmd.help or cmd.brief or "*no description*",
                color = discord.Color.blurple()
            )
            for key, value in cmd.extras.items():
                if key == "category":
                    continue
                cmdEmbed.add_field(name = key, value = value)

            await ctx.reply(embed = cmdEmbed)
        
        #shows a list of all commands
        else:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))