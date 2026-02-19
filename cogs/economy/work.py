import discord
from discord.ext import commands
from discord import app_commands
from database import db, eco
from datetime import timedelta, datetime
from cogs.economy.daily import tdFormatter
from cogs.utility.help import HelpData
from logHandler import loggerSetup

logger = loggerSetup(__name__)


class Work(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    Help = HelpData(
        category="Economy",
        dmOnly=False,
        serverOnly=False,
        subcommands=None,
        permissions=None,
        help=None,
        brief="Works, i guess",
        usage=None,
        aliases=None,
    )

    @commands.command(name="work", **Help.to_kwargs)
    async def work(self, ctx: commands.Context[commands.Bot]):
        # checks the balance and the last work date of the user
        row = await db.fetchone(
            """
            SELECT balance, last_work_date FROM user
            WHERE user_id = ?;
            """,
            (ctx.author.id,),
        )
        # if user has no economy account
        if not row:
            return await ctx.reply(
                "You have no account to work for.\nTry `/daily` to get your first daily and account and try again."
            )

        now = discord.utils.utcnow()

        workDate: datetime | None = (
            datetime.fromisoformat(row["last_work_date"])
            if isinstance(row["last_work_date"], str)
            else row["last_work_date"]
        )

        # if user trys to work within the limited time
        if workDate and workDate + timedelta(minutes=90) > now:
            return await ctx.reply(
                f"You must rest `{tdFormatter(workDate + timedelta(minutes=90) - now)}` to be able to `work` again."
            )

        # updates the user balance
        await db.execute(
            """
            UPDATE user
            SET balance = ?, last_work_date = ?
            WHERE user_id = ?;
            """,
            (row["balance"] + eco.work, now, ctx.author.id),
        )

        # sends the result
        resultEmbed = discord.Embed(
            title="Work ⛏️",
            description=(
                "Good Job !"
                f"\nYou earned **{eco.work}** for working so hard."
                f"You must rest **{tdFormatter(timedelta(minutes=90))}** to fully recover and be able to work again."
            ),
            color=discord.Color.blurple(),
            timestamp=now,
        )
        await ctx.reply(embed=resultEmbed)

    @work.error
    async def work_error(self, ctx: commands.Context[commands.Bot], error: Exception):
        logger.exception(f"❌ something went wrong with work command:")
        await ctx.reply("something went wrong with **work**.")

    # work slash command
    @app_commands.command(name="work", description=Help.brief, extras=Help.extras)
    async def slashWork(self, interaction: discord.Interaction):
        # checks the balance and the last work date of the user
        row = await db.fetchone(
            """
            SELECT balance, last_work_date FROM user
            WHERE user_id = ?;
            """,
            (interaction.user.id,),
        )
        # if user has no economy account
        if not row:
            return await interaction.response.send_message(
                "You have no account to work for.\nTry `/daily` to get your first daily and account and try again.",
                ephemeral=True,
            )

        now = discord.utils.utcnow()

        workDate: datetime | None = (
            datetime.fromisoformat(row["last_work_date"])
            if isinstance(row["last_work_date"], str)
            else row["last_work_date"]
        )

        # if user trys to work within the limited time
        if workDate and workDate + timedelta(minutes=90) > now:
            return await interaction.response.send_message(
                f"You must rest `{tdFormatter(workDate + timedelta(days = 1) - now)}` to be able to `work` again.",
                ephemeral=True,
            )

        # updates the user balance
        await db.execute(
            """
            UPDATE user
            SET balance = ?, last_work_date = ?
            WHERE user_id = ?;
            """,
            (row["balance"] + eco.work, now, interaction.user.id),
        )

        # sends the result
        resultEmbed = discord.Embed(
            title="Work ⛏️",
            description=(
                "Good Job !"
                f"\nYou earned **{eco.work}** for working so hard."
                f"You must rest till **{now + timedelta(minutes = 90)}** to fully recover and be able to work again."
            ),
            color=discord.Color.blurple(),
            timestamp=now,
        )
        await interaction.response.send_message(embed=resultEmbed)

    @slashWork.error
    async def slashWork_error(self, interaction: discord.Interaction, error: Exception):
        logger.exception(f"❌ something went wrong with /work command:")
        try:
            await interaction.response.send_message(
                "something went wrong with **work**.", ephemeral=True
            )
        except discord.InteractionResponded:
            await interaction.followup.send(
                "something went wrong with **work**.", ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Work(bot))
