"""The `balance` command. It can be run via user to see their current balance."""

import discord
from discord import app_commands
from discord.ext import commands

from core.help import *
from core.bank import get_account, create_account
from logHandler import loggerSetup

logger = loggerSetup(__name__)


class Balance(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    Help = HelpData(
        category=CommandCategory.Economy,
        dmOnly=False,
        serverOnly=False,
        subcommands=None,
        permissions=None,
        help=None,
        brief="Shows the balance of the user.",
        usage=None,
        aliases=["bal"],
    )

    @commands.command(name="balance", **Help.kwargs)
    async def balance(self, ctx: commands.Context[commands.Bot]):
        account = await get_account(ctx.author.id)  # trys to fetches user's account
        # if user has no account, creates one
        if not account:
            account = await create_account(user_id=ctx.author.id)

        # sends the result
        resultEmbed = discord.Embed(
            title=f"{ctx.author.mention}'s Balance",
            description=f"*{account.balance_str}*",
            timestamp=discord.utils.utcnow(),
        )
        await ctx.reply(embed=resultEmbed)

    @balance.error
    async def balance_error(
        self, ctx: commands.Context[commands.Bot], error: Exception
    ):
        logger.exception(f"❌ something went wrong with balance command:")
        await ctx.reply("something went wrong with **balance**.")

    # balance slash command
    @app_commands.command(name="balance", description=Help.brief, extras=Help.extras)
    @app_commands.describe(
        hidden="Whether the result should be visible only to you or not."
    )
    async def slashBalance(
        self, interaction: discord.Interaction, hidden: bool = False
    ):
        account = await get_account(
            interaction.user.id
        )  # trys to fetches user's account
        # if user has no account, creates one
        if not account:
            account = await create_account(user_id=interaction.user.id)

        # sends the result
        resultEmbed = discord.Embed(
            title=f"{interaction.user.mention}'s Balance",
            description=f"*{account.balance_str}*",
            timestamp=discord.utils.utcnow(),
        )
        await interaction.response.send_message(embed=resultEmbed, ephemeral=hidden)

    @slashBalance.error
    async def slashBalance_error(
        self, interaction: discord.Interaction, error: Exception
    ):
        logger.exception(f"❌ something went wrong with /balance command:")
        try:
            await interaction.response.send_message(
                "something went wrong with **balance**.", ephemeral=True
            )
        except discord.InteractionResponded:
            await interaction.followup.send(
                "something went wrong with **balance**.", ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Balance(bot))
