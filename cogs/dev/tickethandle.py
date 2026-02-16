import discord
from discord.ext import commands
import json
from database import db, Session
from cogs.utility.help import HelpData
from logHandler import loggerSetup

logger = loggerSetup(__name__)

with open("config.json") as file:
    config = json.load(file)


class TicketHandle(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    Help = HelpData(
        category="Dev",
        subcommands=["respond", "close"],
        help=None,
        brief="Responds to an open Ticket.",
        usage="<subcommand> <ticket ID>",
        aliases=[],
    )

    @commands.command(
        name="tickethandle",
        help=Help.help,
        brief=Help.brief,
        usage=Help.usage,
        aliases=Help.aliases,
        hidden=True,
        extras=Help.extras,
    )
    async def tickethandle(
        self,
        ctx: commands.Context[commands.Bot],
        cmd: str | None,
        ticketId: int | str | None,
    ):
        inGuild = True if ctx.guild else False

        # checks if the user is an admin to use the command
        if str(ctx.author.id) not in config["ADMINS"]:
            return

        # if user has an active responding session
        for session in Session.sessions:
            if session.type != "gambling" and session.userId == ctx.author.id:
                return await ctx.reply(
                    f"You have an open *{session.type}* session. Try closing it and try again."
                )

        # if user entered no subcommand
        if not cmd:
            msg = await ctx.reply("You must enter a subcommand for this command.")
            if inGuild:
                await ctx.message.delete()
                await msg.delete(delay=5)
            return

        cmd = cmd.lower()
        # if user doesn't enter a valid subcommand
        if cmd not in ("respond", "requireinfo", "close"):
            msg = await ctx.reply("Enter a valid subcommand.")
            if inGuild:
                await ctx.message.delete()
                await msg.delete(delay=5)
            return

        # if user doesn't enter a ticket id
        if not ticketId:
            msg = await ctx.reply("You must enter a Ticket ID to take action.")
            if inGuild:
                await ctx.message.delete()
                await msg.delete(delay=5)
            return

        # if user enters an invalid ticket id
        if not isinstance(ticketId, int):
            msg = await ctx.reply("Enter a valid Ticket ID.")
            if inGuild:
                await ctx.message.delete()
                await msg.delete(delay=5)
            return

        # fetches the ticket data
        row = await db.fetchone(
            """
            SELECT * FROM tickets
            WHERE ticket_id = ?;
            """,
            (ticketId,),
        )
        # if ticket with given id doesn't exist
        if not row:
            msg = await ctx.reply("Ticket with given ID doesn't exist.")
            if inGuild:
                await ctx.message.delete()
                await msg.delete(delay=5)
            return

        # fetches the ticket user
        try:
            ticketUser = self.bot.get_user(row["user_id"]) or await self.bot.fetch_user(
                row["user_id"]
            )
        # if ticket user doesn't exist anymore
        except discord.NotFound:
            msg = await ctx.reply("The Ticket creator user doesn't exist anymore.")
            if inGuild:
                await ctx.message.delete()
                await msg.delete(delay=5)

            # deletes the ticket
            await db.execute(
                """
                DELETE FROM tickets
                WHERE ticket_id = ?;
                """,
                (ticketId,),
            )
            return

        channel = ticketUser.dm_channel
        # fetches the message collector message
        try:
            messageCollector = (
                await channel.fetch_message(row["message_collector_id"])
                if channel
                else None
            )
        except discord.NotFound:
            messageCollector = None

        subject = row["subject"]

        # respond subcommand
        if cmd == "respond":
            session = Session(
                type="ticket-responding", userId=ctx.author.id, channelId=ctx.channel.id
            )  # creates a responding session for the admin

            view = TicketRespondView(
                ctx, ticketId, ticketUser, messageCollector, subject, session
            )  # initializes the ticket responding view
            await view.start()

        # close subcommand
        elif cmd == "close":
            # updates the ticket state
            await db.execute(
                """
                UPDATE tickets
                set state = ?, closed_at = ?
                WHERE ticket_id = ?;
                """,
                ("closed", discord.utils.utcnow(), ticketId),
            )

            closedEmbed = discord.Embed(
                title="Ticket Closed 🎫📪",
                description=f"Ticket with ID **{ticketId}** has been closed.",
                color=discord.Color.blurple(),
                timestamp=discord.utils.utcnow(),
            )
            await ctx.reply(embed=closedEmbed)  # sends the notification

    @tickethandle.error
    async def ticket_error(
        self, ctx: commands.Context[commands.Bot], error: commands.CommandError
    ):
        logger.exception(f"❌ something went wrong with tickethandle command:")
        await ctx.reply("something went wrong with **tickethandle**.")

    # the message collecter listener
    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return

        if msg.author.id in Session.tickethandlesession:
            for session in Session.sessions:
                if (
                    session.userId == msg.author.id
                    and session.type == "ticket-responding"
                ):
                    return session.addMessage(msg)


class TicketRespondView(discord.ui.View):
    def __init__(
        self,
        ctx: commands.Context[commands.Bot],
        ticketId: int,
        ticketUser: discord.User,
        messageCollector: discord.Message | None,
        subject: str,
        session: Session,
    ):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.user = ctx.author
        self.ticketId = ticketId
        self.ticketUser = ticketUser
        self.messageCollector = messageCollector
        self.subject = subject
        self.session = session
        self.timestamp = discord.utils.utcnow()

    async def start(self):
        initialEmbed = discord.Embed(
            title="Ticket Response 🎫",
            description=(
                f"You have opened a **Ticket responding** Session for the Ticket with ID **{self.ticketId}**."
                "\nSend as many messages as you want to respond and hit `done` to close the interaction."
            ),
            color=discord.Color.blurple(),
            timestamp=self.timestamp,
        )
        self.msg = await self.ctx.reply(
            embed=initialEmbed, view=self
        )  # sends the initial message

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

        # if no message is sent, session gets canceled
        if not self.session.messages:
            endEmbed = discord.Embed(
                title="Ticket Response 🎫",
                description="You sent no messages, responding session ended.",
                color=discord.Color.dark_gray(),
                timestamp=self.timestamp,
            )
            await self.msg.edit(embed=endEmbed, view=None)

            self.stop()
            return

        desc = (
            f'{self.ticketUser.mention}, An Admin has sent you a response for [this]({self.messageCollector.jump_url}) Ticket with subject: **"{self.subject}"**.'
            if self.messageCollector
            else f'{self.ticketUser.mention}, An Admin has sent you a response for your Ticket with subject: **"{self.subject}"**.'
        )
        sendingEmbed = discord.Embed(
            title="Ticket Response !🎫",
            description=desc,
            color=discord.Color.blurple(),
            timestamp=self.timestamp,
        )
        msg = (
            await self.messageCollector.reply(embed=sendingEmbed)
            if self.messageCollector
            else await self.ticketUser.send(embed=sendingEmbed)
        )  # sends the initial message to the ticket user

        # replys the collected messages to the initial message
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

        # updates the state of the ticket
        await db.execute(
            """
            UPDATE tickets
            SET state = ?, closed_at = ?
            WHERE ticket_id = ?;
            """,
            ("closed", self.timestamp, self.ticketId),
        )

        # sends the succeed message to the admin
        notifyEmbed = discord.Embed(
            title="Ticket Response 🎫",
            description=f"Your Response to the Ticket with ID **{self.ticketId}** has been sent succesfully.",
            color=discord.Color.green(),
            timestamp=self.timestamp,
        )
        await self.msg.edit(embed=notifyEmbed, view=None)

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
        endEmbed = discord.Embed(
            title="Ticket Response 🎫",
            description="You canceled the session.",
            color=discord.Color.dark_gray(),
            timestamp=self.timestamp,
        )
        await self.msg.edit(embed=endEmbed, view=None)

        self.stop()

    async def on_timeout(self):
        # disables buttons on timeout
        for btn in self.children:
            if isinstance(btn, discord.ui.Button):
                btn.disabled = True

        self.session.close()  # ends the session upon timeout

        # sends the timeout message
        toEmbed = discord.Embed(
            title="Ticket Response 🎫",
            description=f"⏰ Ticket Response session timeout.",
            color=discord.Color.dark_gray(),
            timestamp=self.timestamp,
        )
        try:
            await self.msg.edit(embed=toEmbed, view=self)
        except discord.NotFound:
            pass

        self.stop()  # stops the interaction upon timeout

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item[discord.ui.View],
    ):
        self.session.close()  # ends the session upon error

        logger.exception(
            f"❌ something went wrong with tickethandle interaction - button: {getattr(item, 'label', 'unknown')}"
        )
        try:
            await interaction.response.send_message(
                "something went wrong with **tickethandle**.", ephemeral=True
            )
        except discord.InteractionResponded:
            await interaction.followup.send(
                "something went wrong with **tickethandle**.", ephemeral=True
            )
        except Exception:
            pass

        self.stop()  # stops the interaction upon error


async def setup(bot: commands.Bot):
    await bot.add_cog(TicketHandle(bot))
