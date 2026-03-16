import discord
from discord.ext import commands
from discord import app_commands
from database import db
import secrets
import string
from cogs.utility.help import HelpData
from logHandler import loggerSetup

logger = loggerSetup(__name__)

publicIdLength = 12  # the length of the public ids


def idGenerator(length: int):
    characters = string.ascii_letters + string.digits
    return "".join(secrets.choice(characters) for _ in range(length))


async def publicIdGenerator():
    while True:
        publicId = idGenerator(publicIdLength)
        row = await db.fetchone(
            """
            SELECT 1 FROM anonusers
            WHERE public_id = ?
            """,
            (publicId,),
        )
        if not row:
            return publicId


class AnonId(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    Help = HelpData(
        category=HelpData.Category.Anonymous,
        dmOnly=True,
        serverOnly=False,
        subcommands=None,
        permissions=None,
        help=(
            "Shows the public Anonymous ID for the user."
            "\n\nIf user had no ID before, creates one for them."
            "\n\nUser can share this public ID anywhere and people can start sending anonymous messages to them with it. (try `/help anonsend` for more information)"
        ),
        brief="Shows the public Anonymous ID for the user.",
        usage=None,
        aliases=["anonymousid"],
    )

    @commands.command(name="anonid", **Help.to_kwargs)
    async def anonid(self, ctx: commands.Context[commands.Bot]):
        # if user runs the command in a server
        if ctx.guild:
            return await ctx.reply("This command can only be used in Amélie's dm.")

        # trys to fetch user's public id
        row = await db.fetchone(
            """
            SELECT public_id FROM anonusers
            WHERE user_id = ?;
            """,
            (ctx.author.id,),
        )
        # if user id doesn't exist, creates one
        if not row:
            newId = await publicIdGenerator()  # creates an id

            # inserts the new created id
            await db.execute(
                """
                INSERT INTO anonusers (user_id, public_id, created_at)
                VALUES (?, ?, ?);
                """,
                (ctx.author.id, newId, discord.utils.utcnow()),
            )

            publicId = newId

        # if existing public id length is invalid, updates it
        elif len(row["public_id"]) != publicIdLength:
            newId = await publicIdGenerator()  # creates another id with updated length

            await db.execute(
                """
                UPDATE anonusers
                SET public_id = ?
                WHERE user_id = ?;
                """,
                (newId, ctx.author.id),
            )

            publicId = newId

        # public id exists
        else:
            publicId: str = row["public_id"]

        # sends the result
        resultEmbed = discord.Embed(
            title="Anonymous ID",
            description=(
                f"Your anonymous ID is: `{publicId}`"
                "\nShare this somewhere and people can message you anonymously with `/anonsend`."
            ),
            color=discord.Color.blurple(),
        )
        await ctx.reply(embed=resultEmbed)

    @anonid.error
    async def anonid_error(self, ctx: commands.Context[commands.Bot], error: Exception):
        logger.exception(f"❌ something went wrong with anonid command:")
        await ctx.reply("something went wrong with **anonid**.")

    # anonid slash command
    @app_commands.command(name="anonid", description=Help.brief, extras=Help.extras)
    @app_commands.dm_only()
    async def slashAnonid(self, interaction: discord.Interaction):
        # trys to fetch user's public id
        row = await db.fetchone(
            """
            SELECT public_id FROM anonusers
            WHERE user_id = ?;
            """,
            (interaction.user.id,),
        )
        # if user id doesn't exist, creates one
        if not row:
            newId = await publicIdGenerator()  # creates an id

            # inserts the new created id
            await db.execute(
                """
                INSERT INTO anonusers (user_id, public_id, created_at)
                VALUES (?, ?, ?);
                """,
                (interaction.user.id, newId, discord.utils.utcnow()),
            )

            publicId = newId

        # if existing public id length is invalid, updates it
        elif len(row["public_id"]) != publicIdLength:
            newId = await publicIdGenerator()  # creates another id with updated length

            await db.execute(
                """
                UPDATE anonusers
                SET public_id = ?
                WHERE user_id = ?;
                """,
                (newId, interaction.user.id),
            )

            publicId = newId

        # public id exists
        else:
            publicId: str = row["public_id"]

        # sends the result
        resultEmbed = discord.Embed(
            title="Anonymous ID",
            description=(
                f"Your anonymous ID is: `{publicId}`"
                "\nShare this somewhere and people can message you anonymously with `/anonsend`."
            ),
            color=discord.Color.blurple(),
        )
        await interaction.response.send_message(embed=resultEmbed)

    @slashAnonid.error
    async def slashAnonid_error(
        self, interaction: discord.Interaction, error: Exception
    ):
        logger.exception(f"❌ something went wrong with /anonid command:")
        try:
            await interaction.response.send_message(
                "something went wrong with **anonid**.", ephemeral=True
            )
        except discord.InteractionResponded:
            await interaction.followup.send(
                "something went wrong with **anonid**.", ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(AnonId(bot))
