import discord
from discord.ext import commands
from discord import app_commands
from database import db, Session, sessionCheck
from cogs.utility.help import HelpData
from cogs.anonymous.anonid import idGenerator, publicIdLength
from logHandler import loggerSetup

logger = loggerSetup(__name__)

privateIdLength = 6  # the length of the private ids

sessionCache: dict[int, Session] = {}


async def privateIdGenerator(recieverUserId: int):
    while True:
        privateId = idGenerator(privateIdLength)
        row = await db.fetchone(
            """
            SELECT 1 FROM anonusercontact
            WHERE user_id = ? AND contact_anon_id = ?;
            """,
            (recieverUserId, privateId),
        )
        if not row:
            return privateId


class AnonSend(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    Help = HelpData(
        category="Anonymous",
        dmOnly=True,
        help=(
            "Starts an anonymous messaging session, allowing the user to send as many messages as they want anonymously to the target who has shared their public ID."
        ),
        brief="Sends an anonymous message to someone.",
        usage="<public ID>",
        aliases=["anons"],
    )

    @commands.command(
        name="anonsend",
        help=Help.help,
        brief=Help.brief,
        usage=Help.usage,
        aliases=Help.aliases,
        extras=Help.extras,
    )
    async def anonsend(
        self, ctx: commands.Context[commands.Bot], public_id: str | None
    ):
        # if user runs the command in a server
        if ctx.guild:
            return await ctx.reply("This command can only be used in Amélie's dm.")

        # if user has an active session
        session = sessionCheck(
            userId=ctx.author.id, type=Session.Types.anonymoussend, messageBased=True
        )
        if session:
            return await ctx.reply(
                f"You have an open {session.type.value} session, close it first and try again."
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
        row = await db.fetchone(
            """
            SELECT user_id FROM anonusers
            WHERE public_id = ?;
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
        row = await db.fetchone(
            """
            SELECT contact_anon_id, blocked from anonusercontact
            WHERE user_id = ? AND contact_id = ?;
            """,
            (recieverUser.id, ctx.author.id),
        )
        # if user is not in the target's anon contacts, creates one
        if not row:
            newId = await privateIdGenerator(recieverUser.id)
            await db.execute(
                """
                INSERT INTO anonusercontact (user_id, contact_id, contact_anon_id)
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

        sessionCache[ctx.author.id] = Session(
            type=Session.Types.anonymoussend,
            userId=ctx.author.id,
            channelId=ctx.channel.id,
        )  # opens a session

        view = AnonView(
            ctx, recieverUser, public_id, privateId
        )  # initializes the Anon View
        await view.start()

    @anonsend.error
    async def anonsend_error(
        self, ctx: commands.Context[commands.Bot], error: Exception
    ):
        # ends the session upon error
        sessionCache[ctx.author.id].close()
        sessionCache.pop(ctx.author.id)

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
        session = sessionCheck(
            userId=interaction.user.id,
            type=Session.Types.anonymoussend,
            messageBased=True,
        )
        if session:
            return await interaction.response.send_message(
                f"You have an open {session.type.value} session, close it first and try again.",
                ephemeral=True,
            )

        # if user enters an invalid id
        if len(public_id) != publicIdLength:
            return await interaction.response.send_message(
                "Enter a valid public ID.",
                ephemeral=True,
            )

        # checks if a user with given public id exists
        row = await db.fetchone(
            """
            SELECT user_id FROM anonusers
            WHERE public_id = ?;
            """,
            (public_id,),
        )
        # if user with given public id doesn't exist
        if not row:
            return await interaction.response.send_message(
                "User with this ID doesn't exist.",
                ephemeral=True,
            )

        recieverUser = self.bot.get_user(row["user_id"]) or await self.bot.fetch_user(
            row["user_id"]
        )  # fetches the reciever user

        # fetches the reciever's anon contacts
        row = await db.fetchone(
            """
            SELECT contact_anon_id, blocked from anonusercontact
            WHERE user_id = ? AND contact_id = ?;
            """,
            (recieverUser.id, interaction.user.id),
        )
        # if user is not in the target's anon contacts, creates one
        if not row:
            newId = await privateIdGenerator(recieverUser.id)
            await db.execute(
                """
                INSERT INTO anonusercontact (user_id, contact_id, contact_anon_id)
                VALUES (?, ?, ?);
                """,
                (recieverUser.id, interaction.user.id, newId),
            )
            privateId = newId

        # if user contact exists but is blocked
        elif row["blocked"] == 1:
            return await interaction.response.send_message(
                "You can't send anonymous messages to this user.",
                ephemeral=True,
            )

        else:
            privateId: str = row["contact_anon_id"]

        sessionCache[interaction.user.id] = Session(
            type=Session.Types.anonymoussend,
            userId=interaction.user.id,
            channelId=interaction.channel_id,
        )  # opens a session

        view = AnonView(
            interaction, recieverUser, public_id, privateId
        )  # initializes the Anon View
        await view.start()

    @slashAnonsend.error
    async def slashAnonsend_error(
        self, interaction: discord.Interaction, error: Exception
    ):
        # ends the session upon error
        sessionCache[interaction.user.id].close()
        sessionCache.pop(interaction.user.id)

        logger.exception(f"❌ something went wrong with /Anonsend command:")
        try:
            await interaction.response.send_message(
                "something went wrong with **Anonsend**.", ephemeral=True
            )
        except discord.InteractionResponded:
            await interaction.followup.send(
                "something went wrong with **Anonsend**.", ephemeral=True
            )

    # the message collecter listener
    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return
        if msg.guild:
            return

        if msg.author.id in sessionCache:
            sessionCache[msg.author.id].messages.append(msg)


class AnonView(discord.ui.View):
    def __init__(
        self,
        ctx: commands.Context[commands.Bot] | discord.Interaction,
        recieverUser: discord.User,
        public_id: str,
        private_id: str,
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
        if not self.slash:
            self.msg = await self.ctx.reply(embed=initialEmbed, view=self)
            self.msgId = self.msg.id
        else:
            await self.interaction.response.send_message(embed=initialEmbed, view=self)
            msg = await self.interaction.original_response()
            self.msgId = msg.id

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

        await interaction.response.defer()

        now = discord.utils.utcnow()

        sessionCache[self.user.id].close()  # ends the session
        messages = sessionCache.pop(self.user.id).messages  # collects the messages

        # if no message is sent, session gets canceled
        if not messages:
            endEmbed = discord.Embed(
                title="Anonymous Message",
                description="You sent no message, session ended.",
                color=discord.Color.dark_gray(),
                timestamp=now,
            )
            if not self.slash:
                await self.msg.edit(embed=endEmbed, view=None)
            else:
                await self.interaction.edit_original_response(embed=endEmbed, view=None)

            self.stop()
            return

        # creates the session id
        row = await db.fetchone(
            """
            SELECT COALESCE(MAX(session_id), 0) + 1
            FROM anonsessions
            WHERE reciever_id = ? AND sender_id = ?;
            """,
            (self.public_id, self.private_id),
        )
        sessionId: int = row[0] if row else 1

        # stores the session in the database
        await db.execute(
            """
            INSERT INTO anonsessions (session_id, reciever_id, sender_id, sender_message_collector_id, session_date)
            VALUES (?, ?, ?, ?, ?);
            """,
            (sessionId, self.public_id, self.private_id, self.msgId, now),
        )

        # send the messages to the target
        sendingEmbed = discord.Embed(
            title="new Anonymous Message !",
            description=(
                f"User with ID: `{self.private_id}` (Session ID: *{sessionId}*) has sent you these messages:"
            ),
            color=discord.Color.blurple(),
            timestamp=now,
        )
        msg = await self.recieverUser.send(
            embed=sendingEmbed
        )  # sends an initial message to the reciever

        # replys the collected messages
        for m in sessionCache[self.user.id].messages:
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
        notifyEmbed = discord.Embed(
            title="Anonymous Message",
            description=f"Your messages have been sent to `{self.recieverUser.name}` succesfully. (Session ID: *{sessionId}*)",
            color=discord.Color.green(),
            timestamp=now,
        )
        if not self.slash and isinstance(self.msg, discord.Message):
            await self.msg.edit(embed=notifyEmbed, view=None)
        else:
            await self.interaction.edit_original_response(embed=notifyEmbed, view=None)

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

        await interaction.response.defer()

        now = discord.utils.utcnow()

        # ends the session
        sessionCache[self.user.id].close()
        sessionCache.pop(self.user.id)

        # sends the cancel message to the user
        endEmbed = discord.Embed(
            title="Anonymous Message",
            description="You canceled the session.",
            color=discord.Color.dark_gray(),
            timestamp=now,
        )
        if not self.slash:
            await self.msg.edit(embed=endEmbed, view=None)
        else:
            await self.interaction.edit_original_response(embed=endEmbed, view=None)

        self.stop()

    async def on_timeout(self):
        # disables buttons on timeout
        for btn in self.children:
            if isinstance(btn, discord.ui.Button):
                btn.disabled = True

        # ends the session upon timeout
        sessionCache[self.user.id].close()
        sessionCache.pop(self.user.id)

        # sends the timeout message
        toEmbed = discord.Embed(
            title="Anonymous Message", description=f"⏰ Session timeout."
        )
        try:
            if not self.slash and isinstance(self.msg, discord.Message):
                await self.msg.edit(embed=toEmbed, view=self)
            else:
                await self.interaction.edit_original_response(embed=toEmbed, view=self)
        except discord.NotFound:
            pass

        self.stop()

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item[discord.ui.View],
    ):
        # ends the session upon error
        sessionCache[self.user.id].close()
        sessionCache.pop(self.user.id)

        logger.exception(
            f"❌ something went wrong with anonsend interaction - button: {getattr(item, 'label', 'unknown')}"
        )
        try:
            await interaction.response.send_message(
                "something went wrong with **anonsend**.", ephemeral=True
            )
        except discord.InteractionResponded:
            await interaction.followup.send(
                "something went wrong with **anonsend**.", ephemeral=True
            )
        except Exception:
            pass

        self.stop()


async def setup(bot: commands.Bot):
    await bot.add_cog(AnonSend(bot))
