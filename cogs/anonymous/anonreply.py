import discord
from discord.ext import commands
from discord import app_commands
from database import db
from cogs.anonymous.anonsend import privateIdLength
from cogs.utility.help import HelpData
from core.logHandler import loggerSetup

logger = loggerSetup(__name__)


class AnonReply(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    Help = HelpData(
        category=HelpData.Category.Anonymous,
        dmOnly=True,
        serverOnly=False,
        subcommands=None,
        permissions=None,
        help=(
            "Replies to an Anonymous session created via the Anonymous sender."
            "\n\nThe Anonymous sender will recieve the reply message and get notified who responded to their Anonymous session."
        ),
        brief="Replies to an Anonymous session.",
        usage="<private_id> <session_id> <message>",
        aliases=["anonr"],
    )

    @commands.command(name="anonreply", **Help.to_kwargs)
    async def anonreply(
        self,
        ctx: commands.Context[commands.Bot],
        private_id: str | None,
        session_id: int | str | None,
        *,
        message: str | None,
    ):
        # if user runs the command in a server
        if ctx.guild:
            return await ctx.reply("This command can only be used in Amélie's dm.")

        # checks if user has a public id
        row = await db.fetchone(
            """
            SELECT 1 FROM anonusers
            WHERE user_id = ?;
            """,
            (ctx.author.id,),
        )
        if not row:
            return await ctx.reply(
                "You have no public ID so nobody has sent you anything."
            )

        # if user doesn't enter the target's private id
        if not private_id:
            return await ctx.reply(
                "You must enter the private ID of the user you want to reply."
            )

        # if entered private id is invalid
        if len(private_id) != privateIdLength:
            return await ctx.reply("Enter a valid private ID.")

        # checks if target private id is in user's anon contact
        row = await db.fetchone(
            """
            SELECT contact_id, blocked FROM anonusercontact
            WHERE user_id = ? AND contact_anon_id = ?;
            """,
            (ctx.author.id, private_id),
        )
        if not row:
            print(f"{private_id}, {session_id}")
            return await ctx.reply("User with given ID hasn't sent you anything.")

        if row["blocked"]:
            return await ctx.reply(
                "You have blocked this user and can't reply to them anymore."
            )

        try:
            contactUser = self.bot.get_user(
                row["contact_id"]
            ) or await self.bot.fetch_user(
                row["contact_id"]
            )  # fetchs the sender user

        # if user doesn't exist anymore, deletes the contact
        except discord.NotFound:
            await db.execute(
                """
                DELETE FROM anonusercontact
                WHERE user_id = ? AND contact_id = ?;
                """,
                (ctx.author.id, row["contact_id"]),
            )

            return await ctx.reply(
                "The sender with this private ID doesn't exist anymore."
            )

        # if user doesn't enter the session id
        if not session_id:
            return await ctx.reply("You must enter the session ID you want to reply.")
        # if user doesn't enter a valid session id
        if not isinstance(session_id, int):
            return await ctx.reply("Enter a valid session ID.")

        # checks if session id with target private id exists in sessions
        row = await db.fetchone(
            """
            SELECT contact_message_collector_id, responded FROM anonsessions
            WHERE session_id = ? AND reciever_id = ? AND contact_anon_id = ?;
            """,
            (session_id, ctx.author.id, private_id),
        )
        if not row:
            return await ctx.reply("User with given ID had no such session with you.")

        if row["responded"] == 1:
            return await ctx.reply("You have already responded to this session before.")

        # if user doesn't enter any message
        if not message:
            return await ctx.reply(
                "You must enter your message to be replied to this session."
            )

        # fetches the message collecter message
        try:
            messageCollector = await contactUser.fetch_message(
                row["contact_message_collector_id"]
            )
        except discord.NotFound:
            messageCollector = None

        now = discord.utils.utcnow()

        desc = (
            f"`{ctx.author.display_name}` has replied to [this]({messageCollector.jump_url}) Session(Session ID: *{session_id}*):"
            if messageCollector
            else f"`{ctx.author.display_name}` has replied to the Session(Session ID: *{session_id}*):"
        )
        sendingEmbed = discord.Embed(
            title="Anonymous Message",
            description=desc,
            color=discord.Color.blurple(),
            timestamp=now,
        )
        # sends and then replys to the initial notification message
        if messageCollector:
            msg = await messageCollector.reply(embed=sendingEmbed)
            await msg.reply(message)
        else:
            msg = await contactUser.send(embed=sendingEmbed)
            await msg.reply(message)

        # updates session status to responded
        await db.execute(
            """
            UPDATE anonsessions
            SET responded = ?
            WHERE session_id = ? AND reciever_id = ? AND contact_anon_id = ?;
            """,
            (1, session_id, ctx.author.id, private_id),
        )

        resultEmbed = discord.Embed(
            title="Anonymous Message",
            description=f"Your reply message for `{private_id}` with Session(Session ID: *{session_id}*) has been sent.",
            color=discord.Color.green(),
            timestamp=now,
        )
        await ctx.reply(embed=resultEmbed)  # sends the succeed message for the user

    @anonreply.error
    async def anonreply_error(
        self, ctx: commands.Context[commands.Bot], error: Exception
    ):
        logger.exception(f"❌ something went wrong with anonreply command:")
        await ctx.reply("something went wrong with **anonreply**.")

    # anonreply slash command
    @app_commands.command(name="anonreply", description=Help.brief, extras=Help.extras)
    @app_commands.describe(
        private_id="The private ID of the person you want to reply to.",
        session_id="The session ID of the session you want to reply to.",
        message="The message you want to be replied.",
    )
    @app_commands.dm_only()
    async def slashAnonreply(
        self,
        interaction: discord.Interaction,
        private_id: str,
        session_id: int,
        message: str,
    ):
        # checks if user has a public id
        row = await db.fetchone(
            """
            SELECT 1 FROM anonusers
            WHERE user_id = ?;
            """,
            (interaction.user.id,),
        )
        if not row:
            return await interaction.response.send_message(
                "You have no public ID so nobody has sent you anything.", ephemeral=True
            )

        # if entered private id is invalid
        if len(private_id) != privateIdLength:
            return await interaction.response.send_message(
                "Enter a valid private ID.", ephemeral=True
            )

        # checks if target private id is in user's anon contact
        row = await db.fetchone(
            """
            SELECT contact_id, blocked FROM anonusercontact
            WHERE user_id = ? AND contact_anon_id = ?;
            """,
            (interaction.user.id, private_id),
        )
        if not row:
            return await interaction.response.send_message(
                "User with given ID hasn't sent you anything.", ephemeral=True
            )

        if row["blocked"]:
            return await interaction.response.send_message(
                "You have blocked this user and can't reply to them anymore.",
                ephemeral=True,
            )

        try:
            contactUser = self.bot.get_user(
                row["contact_id"]
            ) or await self.bot.fetch_user(
                row["contact_id"]
            )  # fetchs the sender user

        # if user doesn't exist anymore, deletes the contact
        except discord.NotFound:
            await db.execute(
                """
                DELETE FROM anonusercontact
                WHERE user_id = ? AND contact_id = ?;
                """,
                (interaction.user.id, row["contact_id"]),
            )

            return await interaction.response.send_message(
                "The sender with this private ID doesn't exist anymore.", ephemeral=True
            )

        # checks if session id with target private id exists in sessions
        row = await db.fetchone(
            """
            SELECT contact_message_collector_id, responded FROM anonsessions
            WHERE session_id = ? AND reciever_id = ? AND contact_anon_id = ?;
            """,
            (session_id, interaction.user.id, private_id),
        )
        if not row:
            return await interaction.response.send_message(
                "User with given ID had no such session with you.", ephemeral=True
            )

        if row["responded"] == 1:
            return await interaction.response.send_message(
                "You have already responded to this session before.", ephemeral=True
            )

        # fetches the message collecter message
        try:
            messageCollector = await contactUser.fetch_message(
                row["contact_message_collector_id"]
            )
        except discord.NotFound:
            messageCollector = None

        now = discord.utils.utcnow()

        desc = (
            f"`{interaction.user.display_name}` has replied to [this]({messageCollector.jump_url}) Session(Session ID: *{session_id}*):"
            if messageCollector
            else f"`{interaction.user.display_name}` has replied to the Session(Session ID: *{session_id}*):"
        )
        sendingEmbed = discord.Embed(
            title="Anonymous Message",
            description=desc,
            color=discord.Color.blurple(),
            timestamp=now,
        )
        # sends and then replys to the initial notification message
        if messageCollector:
            msg = await messageCollector.reply(embed=sendingEmbed)
            await msg.reply(message)
        else:
            msg = await contactUser.send(embed=sendingEmbed)
            await msg.reply(message)

        # updates session status to responded
        await db.execute(
            """
            UPDATE anonsessions
            SET responded = ?
            WHERE session_id = ? AND reciever_id = ? AND contact_anon_id = ?;
            """,
            (1, session_id, interaction.user.id, private_id),
        )

        resultEmbed = discord.Embed(
            title="Anonymous Message",
            description=f"Your reply message for `{private_id}` with Session(Session ID: *{session_id}*) has been sent.",
            color=discord.Color.green(),
            timestamp=now,
        )
        await interaction.response.send_message(
            embed=resultEmbed
        )  # sends the succeed message for the user

    @slashAnonreply.error
    async def slashAnonreply_error(
        self, interaction: discord.Interaction, error: Exception
    ):
        logger.exception(f"❌ something went wrong with /anonreply command:")
        try:
            await interaction.response.send_message(
                "something went wrong with **anonreply**.", ephemeral=True
            )
        except discord.InteractionResponded:
            await interaction.followup.send(
                "something went wrong with **anonreply**.", ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(AnonReply(bot))
