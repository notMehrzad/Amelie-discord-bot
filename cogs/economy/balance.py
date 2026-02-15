import discord
from discord.ext import commands
from discord import app_commands
from database import db, eco
from cogs.utility.help import HelpData
from logHandler import loggerSetup

logger = loggerSetup(__name__)


class Balance(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    Help: HelpData = {
        "help": "",
        "brief": "Shows the balance of the user.",
        "usage": "",
        "aliases": ["bal"],
        "extras": {"Category": "Economy"},
    }

    @commands.command(
        name="balance",
        help=Help["help"],
        brief=Help["brief"],
        usage=Help["usage"],
        aliases=Help["aliases"],
        extras=Help["extras"],
    )
    async def balance(self, ctx: commands.Context[commands.Bot]):
        # checks if the user has an account already
        row = await db.fetchone(
            """
            SELECT balance FROM user
            WHERE user_id = ?;
            """,
            (ctx.author.id,),
        )
        now = discord.utils.utcnow()
        # if user has no account, creates one
        if not row:
            await db.execute(
                """
                INSERT INTO user (user_id, balance, created_date)
                VALUES (?, ?, ?);
                """,
                (ctx.author.id, 0, now),
            )
            balance = 0
        else:
            balance = row["balance"]

        # sends the result
        resultEmbed = discord.Embed(
            title=f"{ctx.author.display_name}'s Balance",
            description=f"*{balance} {eco.currency_postfix}*",
            timestamp=now,
        )
        await ctx.reply(embed=resultEmbed)

    @balance.error
    async def balance_error(
        self, ctx: commands.Context[commands.Bot], error: Exception
    ):
        logger.exception(f"❌ something went wrong with balance command:")
        await ctx.reply("something went wrong with **balance**.")

    # balance slash command
    @app_commands.command(
        name="balance", description=Help["brief"], extras=Help["extras"]
    )
    @app_commands.describe(
        hidden="Whether the result should be visible only to you or not."
    )
    async def slashBalance(
        self, interaction: discord.Interaction, hidden: bool = False
    ):
        # checks if the user has an account already
        row = await db.fetchone(
            """
            SELECT balance FROM user
            WHERE user_id = ?;
            """,
            (interaction.user.id,),
        )
        now = discord.utils.utcnow()
        # if user has no account, creates one
        if not row:
            await db.execute(
                """
                INSERT INTO user (user_id, balance, created_date)
                VALUES (?, ?, ?);
                """,
                (interaction.user.id, 0, now),
            )
            balance = 0
        else:
            balance = row["balance"]

        # sends the result
        resultEmbed = discord.Embed(
            title=f"{interaction.user.display_name}'s Balance",
            description=f"*{balance} {eco.currency_postfix}*",
            timestamp=now,
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
