import discord
from discord.ext import commands
from discord import app_commands
import random
from cogs.utility.help import HelpData
from logHandler import loggerSetup

logger = loggerSetup(__name__)

class Choose(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    Help: HelpData = {
        "help": "",
        "brief": "Chooses one option between given choices",
        "usage": "<choices (separated with \"|\")>",
        "aliases": [],
        "extras": {"Category": "Utility"}
    }

    @commands.command(
            name = "choose",
            help = Help["help"],
            brief = Help["brief"],
            usage = Help["usage"],
            aliases = Help["aliases"],
            extras = Help["extras"]
    )
    async def choose(self, ctx: commands.Context[commands.Bot], *, choices: str | None):
        #if user doesn't enter any options
        if not choices:
            return await ctx.reply("You must enter at least two choices separated with \"|\".")
        
        choicesList = [c.strip() for c in choices.split("|") if c.strip()] #fetches the options

        #if user doesn't enter at least two options to choose
        if len(choicesList) < 2:
            return await ctx.reply("You must enter at least two choices separated with \"|\".")
        
        choice = random.choice(choicesList) #makes a choice
        await ctx.reply(f"I'd go with: {choice}") #sends the result

    @choose.error
    async def choose_error(self, ctx: commands.Context[commands.Bot], error: Exception):
        logger.exception(f"❌ something went wrong with choose command:")
        await ctx.reply("something went wrong with **choose**.")

    #choose slash command
    @app_commands.command(
        name = "choose",
        description = Help["brief"],
        extras = Help["extras"]
    )
    @app_commands.describe(choices = "The choices to choose from, separated with \"|\".")
    async def slashChoose(self, interaction: discord.Interaction, choices: str):
        choicesList = [c.strip() for c in choices.split("|") if c.strip()] #fetches the options

        #if user doesn't enter at least two options to choose
        if len(choicesList) < 2:
            return await interaction.response.send_message("You must enter at least two choices separated with \"|\".", ephemeral = True)
        
        choice = random.choice(choicesList) #makes a choice
        await interaction.response.send_message(f"I'd go with: {choice}") #sends the result

    @slashChoose.error
    async def slashChoose_error(self, interaction: discord.Interaction, error: Exception):
        logger.exception(f"❌ something went wrong with /choose command:")
        try:
            await interaction.response.send_message("something went wrong with **choose**.", ephemeral = True)
        except discord.InteractionResponded:
            await interaction.followup.send("something went wrong with **choose**.", ephemeral = True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Choose(bot))