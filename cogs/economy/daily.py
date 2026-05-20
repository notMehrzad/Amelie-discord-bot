"""The `daily` command. It is used by users to claim the daily reward."""

from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands

from core.bank import create_account, get_account
from core.database import execute
from core.help import *
from core.logHandler import loggerSetup
from core.utils import timedelta_formater

DAILY_AMOUNT = 500
DAILY_COOLDOWN = 24 * 60  # minutes

logger = loggerSetup(__name__)


class Daily(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    Help = HelpData(
        category=CommandCategory.ECONOMY,
        dmOnly=False,
        serverOnly=False,
        subcommands=None,
        permissions=None,
        help=None,
        brief="Claims the Daily Reward for the user.",
        usage=None,
        aliases=["d"],
    )

    @commands.command(name="daily", **Help.kwargs)
    async def daily(self, ctx: commands.Context[commands.Bot]):
        now = discord.utils.utcnow()

        # trys to fetch the user's account
        account = await get_account(ctx.author.id)

        # if user has no account, creates one
        if not account:
            account = await create_account(user_id=ctx.author.id)

        # if user trys to claim 2 dailies within a day
        if (
            account.last_daily_date
            and account.last_daily_date + timedelta(minutes=DAILY_COOLDOWN) > now
        ):
            await ctx.reply(
                f"You must wait `{timedelta_formater(account.last_daily_date + timedelta(minutes=DAILY_COOLDOWN) - now)}` to claim your next Daily reward."
            )
            return

        # deposits the daily reward
        await account.deposit(
            DAILY_AMOUNT, reason="Daily reward."
        )  # deposits the daily

        # updates the last daily date
        await execute(
            """
            UPDATE bank_accounts
            SET last_daily_date = ?
            WHERE user_id = ?;
            """,
            (int(now.timestamp()), ctx.author.id),
        )

        # sends the result
        resultEmbed = discord.Embed(
            title="Daily Reward !",
            description=(
                f"You have claimed your Daily reward for today."
                f"\nCurrent balance: *{account.balance_str}*"
            ),
            color=discord.Color.blurple(),
            timestamp=now,
        )
        await ctx.reply(embed=resultEmbed)

    @daily.error
    async def daily_error(self, ctx: commands.Context[commands.Bot], error: Exception):
        logger.exception(f"❌ something went wrong with daily command:")
        await ctx.reply("something went wrong with **daily**.")

    # daily slash command
    @app_commands.command(name="daily", description=Help.brief, extras=Help.extras)
    async def slashDaily(self, interaction: discord.Interaction):
        now = discord.utils.utcnow()

        # trys to fetch the user's account
        account = await get_account(interaction.user.id)

        # if user has no account, creates one
        if not account:
            account = await create_account(user_id=interaction.user.id)

        # if user trys to claim 2 dailies within a day
        if (
            account.last_daily_date
            and account.last_daily_date + timedelta(minutes=DAILY_COOLDOWN) > now
        ):
            await interaction.response.send_message(
                f"You must wait `{timedelta_formater(account.last_daily_date + timedelta(minutes=DAILY_COOLDOWN) - now)}` to claim your next Daily reward.",
                ephemeral=True,
            )
            return

        # deposits the daily reward
        await account.deposit(
            DAILY_AMOUNT, reason="Daily reward."
        )  # deposits the daily

        # updates the last daily date
        await execute(
            """
            UPDATE bank_accounts
            SET last_daily_date = ?
            WHERE user_id = ?;
            """,
            (int(now.timestamp()), interaction.user.id),
        )

        # sends the result
        resultEmbed = discord.Embed(
            title="Daily Reward !",
            description=(
                f"You have claimed your Daily reward for today."
                f"\nCurrent balance: *{account.balance_str}*"
            ),
            color=discord.Color.blurple(),
            timestamp=now,
        )
        await interaction.response.send_message(embed=resultEmbed)

    @slashDaily.error
    async def slashDaily_error(
        self, interaction: discord.Interaction, error: Exception
    ):
        logger.exception(f"❌ something went wrong with /daily command:")
        try:
            await interaction.response.send_message(
                "something went wrong with **daily**.", ephemeral=True
            )
        except discord.InteractionResponded:
            await interaction.followup.send(
                "something went wrong with **daily**.", ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Daily(bot))
