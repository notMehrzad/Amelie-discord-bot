import discord
from discord import app_commands
from discord.ext import commands

from cogs.anonymous.anonid import idGenerator, publicIdLength
from cogs.utility.help import HelpData
from core.database import Session, execute, fetchone
from core.dbconstants import AnonContactTable, AnonSessionTable, AnonUserTable
from core.log_handler import logger_setup

logger = logger_setup(__name__)

privateIdLength = 6  # the length of the private ids


async def privateIdGenerator(recieverUserId: int):
    while True:
        privateId = idGenerator(privateIdLength)
        row = await fetchone(
            f"""
            SELECT 1 FROM {AnonContactTable.TABLE_NAME}
            WHERE {AnonContactTable.COL_USER_ID} = ? AND {AnonContactTable.COL_CONTACT_ANON_ID} = ?;
            """,
            (recieverUserId, privateId),
        )
        if not row:
            return privateId


class AnonSend(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    Help = HelpData(
        category=HelpData.Category.Anonymous,
        dm_only=True,
        serverOnly=False,
        subcommands=None,
        permissions=None,
        help=(
            "Starts an Anonymous messaging session."
            "\n\nUser can send as many messages as they want and send them anonymously to the recipient."
            "\n\nRecipient won't know the sender identity but a private anonymous ID spetialized for the sender."
            "\n\nRecipient can reply to this session later if they want to. (try `/help anonreply` for more information)"
        ),
        brief="Sends an Anonymous message.",
        usage="<public_id>",
        aliases=["anons"],
    )

    @commands.command(name="anonsend", **Help.to_kwargs)
    async def anonsend(
        self, ctx: commands.Context[commands.Bot], public_id: str | None
    ):
        # if user runs the command in a server
        if ctx.guild:
            return await ctx.reply("This command can only be used in Amélie's dm.")

        # if user has an active session
        if (ctx.author.id, Session.Types.messaging) in Session.sessions:
            return await ctx.reply(
                "You have an open messaging session, close it first and try again."
            )

        # if user doesn't enter any id
        if not public_id:
            return await ctx.reply(
                "You must enter the user's Public ID to send anonymous message to."
            )

        # if user enters an invalid id
        if len(public_id) != publicIdLength:
            return await ctx.reply("Enter a valid public ID.")

        # checks if a user with given public id exists
        row = await fetchone(
            f"""
            SELECT {AnonUserTable.COL_USER_ID} FROM {AnonUserTable.TABLE_NAME}
            WHERE {AnonUserTable.COL_PUBLIC_ID} = ?;
            """,
            (public_id,),
        )
        # if user with given public id doesn't exist
        if not row:
            return await ctx.reply("User with this ID doesn't exist.")

        recieverUser = self.bot.get_user(row["user_id"]) or await self.bot.fetch_user(
            row["user_id"]
        )  # fetches the reciever user

        # fetches the reciever's anon contacts
        row = await fetchone(
            f"""
            SELECT {AnonContactTable.COL_CONTACT_ANON_ID}, {AnonContactTable.COL_BLOCKED} from {AnonContactTable.TABLE_NAME}
            WHERE {AnonContactTable.COL_USER_ID} = ? AND {AnonContactTable.COL_CONTACT_ID} = ?;
            """,
            (recieverUser.id, ctx.author.id),
        )
        # if user is not in the target's anon contacts, creates one
        if not row:
            newId = await privateIdGenerator(recieverUser.id)
            await execute(
                f"""
                INSERT INTO {AnonContactTable.TABLE_NAME} ({AnonContactTable.columns()})
                VALUES (?, ?, ?);
                """,
                (recieverUser.id, ctx.author.id, newId),
            )
            privateId = newId

        # if user contact exists but is blocked
        elif row["blocked"] == 1:
            return await ctx.reply("You can't send anonymous messages to this user.")

        else:
            privateId: str = row["contact_anon_id"]

        Session(userId=ctx.author.id, type=Session.Types.messaging)  # opens a session

        view = AnonView(
            ctx, recieverUser, public_id, privateId, self.bot
        )  # initializes the Anon View
        await view.start()

    @anonsend.error
    async def anonsend_error(
        self, ctx: commands.Context[commands.Bot], error: Exception
    ):
        try:
            Session.sessions[
                (ctx.author.id, Session.Types.messaging)
            ].close()  # ends the session upon error
        except KeyError:
            pass

        logger.exception(f"❌ something went wrong with anonsend command:")
        await ctx.reply("something went wrong with **anonsend**.")

    # anonsend slash command
    @app_commands.command(name="anonsend", description=Help.brief, extras=Help.extras)
    @app_commands.describe(
        public_id="The public ID of the person you want to send anonymous message to."
    )
    @app_commands.dm_only()
    async def slashAnonsend(self, interaction: discord.Interaction, public_id: str):
        # if user has an active session
        if (interaction.user.id, Session.Types.messaging) in Session.sessions:
            return await interaction.response.send_message(
                "You have an open messaging session, close it first and try again.",
                ephemeral=True,
            )

        # if user enters an invalid id
        if len(public_id) != publicIdLength:
            return await interaction.response.send_message(
                "Enter a valid public ID.", ephemeral=True
            )

        # checks if a user with given public id exists
        row = await fetchone(
            f"""
            SELECT {AnonUserTable.COL_USER_ID} FROM {AnonUserTable.TABLE_NAME}
            WHERE {AnonUserTable.COL_PUBLIC_ID} = ?;
            """,
            (public_id,),
        )
        # if user with given public id doesn't exist
        if not row:
            return await interaction.response.send_message(
                "User with this ID doesn't exist.", ephemeral=True
            )

        recieverUser = self.bot.get_user(row["user_id"]) or await self.bot.fetch_user(
            row["user_id"]
        )  # fetches the reciever user

        # fetches the reciever's anon contacts
        row = await fetchone(
            f"""
            SELECT {AnonContactTable.COL_CONTACT_ANON_ID}, {AnonContactTable.COL_BLOCKED} from {AnonContactTable.TABLE_NAME}
            WHERE {AnonContactTable.COL_USER_ID} = ? AND {AnonContactTable.COL_CONTACT_ID} = ?;
            """,
            (recieverUser.id, interaction.user.id),
        )
        # if user is not in the target's anon contacts, creates one
        if not row:
            newId = await privateIdGenerator(recieverUser.id)
            await execute(
                f"""
                INSERT INTO {AnonContactTable.TABLE_NAME} ({AnonContactTable.columns()})
                VALUES (?, ?, ?);
                """,
                (recieverUser.id, interaction.user.id, newId),
            )
            privateId = newId

        # if user contact exists but is blocked
        elif row["blocked"] == 1:
            return await interaction.response.send_message(
                "You can't send anonymous messages to this user.", ephemeral=True
            )

        else:
            privateId: str = row["contact_anon_id"]

        Session(
            userId=interaction.user.id, type=Session.Types.messaging
        )  # opens a session

        view = AnonView(
            interaction, recieverUser, public_id, privateId, self.bot
        )  # initializes the Anon View
        await view.start()

    @slashAnonsend.error
    async def slashAnonsend_error(
        self, interaction: discord.Interaction, error: Exception
    ):
        try:
            Session.sessions[
                (interaction.user.id, Session.Types.messaging)
            ].close()  # ends the session upon error
        except KeyError:
            pass

        logger.exception(f"❌ something went wrong with /Anonsend command:")
        (
            await interaction.response.send_message(
                "something went wrong with **anonsend**.", ephemeral=True
            )
            if not interaction.response.is_done()
            else await interaction.followup.send(
                "something went wrong with **anonsend**.", ephemeral=True
            )
        )


class AnonView(discord.ui.View):
    def __init__(
        self,
        ctx: commands.Context[commands.Bot] | discord.Interaction,
        recieverUser: discord.User,
        public_id: str,
        private_id: str,
        bot: commands.Bot,
    ):
        super().__init__(timeout=300)
        if isinstance(ctx, discord.Interaction):
            self.slash = True
            self.interaction = ctx
            self.user = ctx.user
        else:
            self.slash = False
            self.ctx = ctx
            self.user = ctx.author
        self.recieverUser = recieverUser
        self.public_id = public_id
        self.private_id = private_id
        self.bot = bot
        self.session = Session.sessions[(self.user.id, Session.Types.messaging)]

    async def start(self):
        initialEmbed = discord.Embed(
            title="Anonymous Message",
            description=(
                f"You are texting `{self.recieverUser.display_name}` anonymously."
                "\nSend as many messages as you want and hit `done` to close the interaction."
            ),
            color=discord.Color.blurple(),
        )
        # sends the initial message and stores channel and message id
        if self.slash:
            await self.interaction.response.send_message(embed=initialEmbed, view=self)
            msg = await self.interaction.original_response()
            self.msgId = msg.id
        else:
            self.msg = await self.ctx.reply(embed=initialEmbed, view=self)
            self.msgId = self.msg.id

        await self.session.collectMessage(
            self.bot, dmOnly=True
        )  # starts collecting messages

    # done button
    @discord.ui.button(label="done", style=discord.ButtonStyle.green, row=0)
    async def done(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button[discord.ui.View],
    ):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(
                "You can't control this session.", ephemeral=True
            )

        self.session.close()  # ends the session

        timestamp = discord.utils.utcnow()

        # if no message is sent, session gets canceled
        if not self.session.messages:
            cancelEmbed = discord.Embed(
                title="Anonymous Message",
                description="You sent no message, session ended.",
                color=discord.Color.dark_gray(),
                timestamp=timestamp,
            )
            await interaction.response.edit_message(embed=cancelEmbed, view=None)

            self.stop()
            return

        # creates the session id
        row = await fetchone(
            f"""
            SELECT COALESCE(MAX({AnonSessionTable.COL_SESSION_ID}), 0) + 1
            FROM {AnonSessionTable.TABLE_NAME}
            WHERE {AnonSessionTable.COL_RECEIVER_ID} = ? AND {AnonSessionTable.COL_CONTACT_ANON_ID} = ?;
            """,
            (self.recieverUser.id, self.private_id),
        )
        sessionId: int = row[0] if row else 1

        # stores the session in the database
        await execute(
            f"""
            INSERT INTO {AnonSessionTable.TABLE_NAME} ({AnonSessionTable.columns()})
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (sessionId, self.recieverUser.id, self.private_id, self.msgId, timestamp),
        )

        await interaction.response.defer()

        # send the messages to the target
        recieverNotifEmbed = discord.Embed(
            title="New Anonymous Message !",
            description=(
                f"User with ID: `{self.private_id}` (Session ID: *{sessionId}*) has sent you these messages:"
            ),
            color=discord.Color.blurple(),
            timestamp=timestamp,
        )
        msg = await self.recieverUser.send(
            embed=recieverNotifEmbed
        )  # sends an initial message to the reciever

        # replies the collected messages
        for m in self.session.messages:
            # if message is sticker
            if m.stickers:
                for s in m.stickers:
                    await msg.reply(s.url)
                break

            # if message is text, file or embed or combinations of them
            content = m.content
            files = [await a.to_file() for a in m.attachments]

            await msg.reply(content=content, files=files, embeds=m.embeds)

        # sends the succeed message to the user
        senderNotifEmbed = discord.Embed(
            title="Anonymous Message",
            description=f"Your messages have been sent to `{self.recieverUser.name}` succesfully. (Session ID: *{sessionId}*)",
            color=discord.Color.green(),
            timestamp=timestamp,
        )
        # await interaction.response.edit_message(embed=senderNotifEmbed, view=None)

        await interaction.edit_original_response(embed=senderNotifEmbed, view=None)

        self.stop()

    # cancel button
    @discord.ui.button(label="cancel", style=discord.ButtonStyle.gray, row=0)
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button[discord.ui.View],
    ):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(
                "You can't control this session.", ephemeral=True
            )

        self.session.close()  # ends the session

        # sends the cancel message to the user
        cancelEmbed = discord.Embed(
            title="Anonymous Message",
            description="You canceled the session.",
            color=discord.Color.dark_gray(),
            timestamp=discord.utils.utcnow(),
        )
        await interaction.response.edit_message(embed=cancelEmbed, view=None)

        self.stop()

    async def on_timeout(self):
        # disables buttons on timeout
        for btn in self.children:
            if isinstance(btn, discord.ui.Button):
                btn.disabled = True

        self.session.close()  # ends the session upon timeout

        # sends the timeout message
        timeoutEmbed = discord.Embed(
            title="Anonymous Message", description=f"⏰ Session timeout."
        )
        try:
            if self.slash:
                await self.interaction.edit_original_response(
                    embed=timeoutEmbed, view=self
                )
            else:
                await self.msg.edit(embed=timeoutEmbed, view=self)
        except discord.NotFound:
            pass

        self.stop()

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item[discord.ui.View],
    ):
        self.session.close()  # ends the session upon error

        logger.exception(
            f"❌ something went wrong with anonsend interaction - button: {getattr(item, 'label', 'unknown')}"
        )
        (
            await interaction.response.send_message(
                "something went wrong with **anonsend**.", ephemeral=True
            )
            if not interaction.response.is_done()
            else await interaction.followup.send(
                "something went wrong with **anonsend**.", ephemeral=True
            )
        )

        self.stop()


async def setup(bot: commands.Bot):
    await bot.add_cog(AnonSend(bot))
