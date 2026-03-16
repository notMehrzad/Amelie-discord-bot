import discord
from discord.ext import commands
from discord import app_commands
from database import db
from cogs.utility.help import HelpData
from logHandler import loggerSetup

logger = loggerSetup(__name__)


class Lottery(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    Help = HelpData(
        category=HelpData.Category.Economy,
        dmOnly=False,
        serverOnly=False,
        subcommands=None,
        permissions=None,
        help=None,
        brief="Signs in for the lottery.",
        usage=None,
        aliases=None,
    )

    @commands.command(name="lottery", **Help.to_kwargs)
    async def lottery(self, ctx: commands.Context[commands.Bot]):
        # checks if user has already signed in for lottery
        row = await db.fetchone(
            """
            SELECT signed_at FROM lottery
            WHERE user_id = ?;
            """,
            (ctx.author.id,),
        )
        if row:
            return await ctx.reply(
                f"You have already signed in for Lottery at `{row["signed_at"]}`."
            )

        # signs the user for the lottery
        await db.execute(
            """
            INSERT INTO lottery (user_id, signed_at)
            VALUES (?, ?);
            """,
            (ctx.author.id, discord.utils.utcnow()),
        )
        await ctx.reply("You have signed in for the Lottery successfully. Be tuned.")

    @lottery.error
    async def lottery_error(
        self, ctx: commands.Context[commands.Bot], error: commands.CommandError
    ):
        logger.exception(f"❌ something went wrong with lottery command:")
        await ctx.reply("something went wrong with **lottery**.")

    # lottery slash command
    @app_commands.command(name="lottery", description=Help.brief, extras=Help.extras)
    async def slashLottery(self, interaction: discord.Interaction):
        # checks if user has already signed in for lottery
        row = await db.fetchone(
            """
            SELECT signed_at FROM lottery
            WHERE user_id = ?;
            """,
            (interaction.user.id,),
        )
        if row:
            return await interaction.response.send_message(
                f"You have already signed in for Lottery at `{row["signed_at"]}`.",
                ephemeral=True,
            )

        # signs the user for the lottery
        await db.execute(
            """
            INSERT INTO lottery (user_id, signed_at)
            VALUES (?, ?);
            """,
            (interaction.user.id, discord.utils.utcnow()),
        )
        await interaction.response.send_message(
            "You have signed in for the Lottery successfully. Be tuned."
        )

    @slashLottery.error
    async def slashLottery_error(
        self, interaction: discord.Interaction, error: Exception
    ):
        logger.exception(f"❌ something went wrong with /lottery command:")
        try:
            await interaction.response.send_message(
                "something went wrong with **lottery**.", ephemeral=True
            )
        except discord.InteractionResponded:
            await interaction.followup.send(
                "something went wrong with **lottery**.", ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Lottery(bot))
