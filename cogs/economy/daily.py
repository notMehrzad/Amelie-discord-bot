"""The `daily` command. It is used by users to claim the daily reward."""

from datetime import timedelta
from typing import final

import discord
from discord import app_commands
from discord.app_commands.errors import AppCommandError
from discord.ext import commands

from core.bank import create_account, get_account
from core.database import execute
from core.dbconstants import AccountTable
from core.help import HelpData
from core.log_handler import logger_setup
from core.utils import timedelta_formater

DAILY_AMOUNT = 500
DAILY_COOLDOWN = 24 * 60  # minutes

logger = logger_setup(__name__)


@final
class Daily(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    Help = HelpData(
        category=HelpData.CommandCategory.ECONOMY,
        dm_only=False,
        serverOnly=False,
        subcommands=None,
        permissions=None,
        help=None,
        brief="Claims the Daily Reward for the user.",
        usage=None,
        aliases=["d"],
    )

    @commands.command(name="daily", **Help.kwargs)
    async def daily(self, ctx: commands.Context[commands.Bot]) -> None:
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
            _ = await ctx.reply(
                f"You must wait `{timedelta_formater(account.last_daily_date + timedelta(minutes=DAILY_COOLDOWN) - now)}` to claim your next Daily reward."
            )
            return

        # deposits the daily reward
        _ = await account.deposit(
            DAILY_AMOUNT, reason="Daily reward."
        )  # deposits the daily

        # updates the last daily date
        await execute(
            f"""
            UPDATE {AccountTable.TABLE_NAME}
            SET {AccountTable.COL_LAST_DAILY_DATE} = ?
            WHERE {AccountTable.COL_USER_ID} = ?;
            """,
            (int(now.timestamp()), ctx.author.id),
        )

        # sends the result
        result_embed = discord.Embed(
            title="Daily Reward !",
            description=(
                f"You have claimed your Daily reward for today."
                f"\nCurrent balance: *{account.balance_str}*"
            ),
            color=discord.Color.blurple(),
            timestamp=now,
        )
        _ = await ctx.reply(embed=result_embed)

    @daily.error
    async def daily_error(
        self, ctx: commands.Context[commands.Bot], error: Exception
    ) -> None:
        logger.exception("❌ something went wrong with daily command:")
        _ = await ctx.reply("something went wrong with **daily**.")

    # daily slash command
    @app_commands.command(name="daily", description=Help.brief, extras=Help.extras)
    async def slash_daily(self, interaction: discord.Interaction) -> None:
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
            _ = await interaction.response.send_message(
                f"You must wait `{timedelta_formater(account.last_daily_date + timedelta(minutes=DAILY_COOLDOWN) - now)}` to claim your next Daily reward.",
                ephemeral=True,
            )
            return

        # deposits the daily reward
        _ = await account.deposit(
            DAILY_AMOUNT, reason="Daily reward."
        )  # deposits the daily

        # updates the last daily date
        await execute(
            f"""
            UPDATE {AccountTable.TABLE_NAME}
            SET {AccountTable.COL_LAST_DAILY_DATE} = ?
            WHERE {AccountTable.COL_USER_ID} = ?;
            """,
            (int(now.timestamp()), interaction.user.id),
        )

        # sends the result
        result_embed = discord.Embed(
            title="Daily Reward !",
            description=(
                f"You have claimed your Daily reward for today."
                f"\nCurrent balance: *{account.balance_str}*"
            ),
            color=discord.Color.blurple(),
            timestamp=now,
        )
        _ = await interaction.response.send_message(embed=result_embed)

    @slash_daily.error
    async def slash_daily_error(
        self, interaction: discord.Interaction, error: AppCommandError
    ) -> None:
        logger.exception("❌ something went wrong with /daily command:")
        try:
            _ = await interaction.response.send_message(
                "something went wrong with **daily**.", ephemeral=True
            )
        except discord.InteractionResponded:
            await interaction.followup.send(
                "something went wrong with **daily**.", ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Daily(bot))
