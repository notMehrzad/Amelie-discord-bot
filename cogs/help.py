import discord
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
            name = "help",
            aliases = ["h"],
            help = (
                "Shows the help menu which gives a brief information about Commands."
                "\nEnter a Command name for its full detail such as its application, usage, necessery permissions (if any) and etc. or don't, to get the help menu."
            ),
            brief = "Shows the help menu.",
            usage = f"<command_name*[optional]*>",
            extras = {"Category": "General"}
    )
    async def help(self, ctx: commands.Context[commands.Bot], cmdStr: str | None = None):
        #help for specific command
        if cmdStr and cmdStr.lower() not in ["all", "list", "menu"]:
            cmd = self.bot.get_command(cmdStr.lower()) #fetches the command, None if not found

            #if user doesn't enter a valid command name
            if not cmd:
                return await ctx.reply(f"*{cmdStr}* doesn't exist. enter a valid command.")
            
            cmdEmbed = discord.Embed(
                title = f"Help: {cmd.name}",
                description = cmd.help or cmd.brief or "*no description*",
                color = discord.Color.blurple()
            )
            #if command has aliases
            if cmd.aliases:
                cmdEmbed.add_field(name = "Aliases", value = ", ".join(cmd.aliases))
            
            if cmd.usage:
                cmdEmbed.add_field(name = "Usage", value = cmd.name + " " + cmd.usage)
            #if command has extra information
            for key, value in cmd.extras.items():
                if key == "Category":
                    continue
                cmdEmbed.add_field(name = key, value = value) #add extra information to fields

            await ctx.reply(embed = cmdEmbed)
        
        #shows the help menu
        else:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))