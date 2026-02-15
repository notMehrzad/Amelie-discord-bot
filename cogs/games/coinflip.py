import discord
from discord.ext import commands
from discord import app_commands
import random
from cogs.utility.help import HelpData
from logHandler import loggerSetup

logger = loggerSetup(__name__)


class CoinFlip(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    Help = HelpData(
        category="Games",
        help=None,
        brief="Flips a coin.",
        usage=None,
        aliases=["cf", "coinf"],
    )

    @commands.command(
        name="coinflip",
        help=Help.help,
        brief=Help.brief,
        usage=Help.usage,
        aliases=Help.aliases,
        extras=Help.extras,
    )
    async def coinflip(self, ctx: commands.Context[commands.Bot]):
        result = random.choice(("Heads", "Tails"))  # flips the coin
        await ctx.reply(result + ".")  # sends the result

    @coinflip.error
    async def coinflip_error(
        self, ctx: commands.Context[commands.Bot], error: Exception
    ):
        logger.exception(f"❌ something went wrong with coinflip command:")
        await ctx.reply("something went wrong with **coinflip**.")

    # coinflip slash command
    @app_commands.command(name="coinflip", description=Help.brief, extras=Help.extras)
    async def slashCoinflip(self, interaction: discord.Interaction):
        result = random.choice(("Heads", "Tails"))  # flips the coin
        await interaction.response.send_message(result + ".")  # sends the result

    @slashCoinflip.error
    async def slashCoinflip_error(
        self, interaction: discord.Interaction, error: Exception
    ):
        logger.exception(f"❌ something went wrong with /coinflip command:")
        try:
            await interaction.response.send_message(
                "something went wrong with **coinflip**.", ephemeral=True
            )
        except discord.InteractionResponded:
            await interaction.followup.send(
                "something went wrong with **coinflip**.", ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(CoinFlip(bot))
