import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
from database import connection
from cogs.utility.help import HelpData
from logHandler import loggerSetup

logger = loggerSetup(__name__)

sessions: dict[int, list[discord.Message]] = {}

class TicketRespond(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    Help: HelpData = {
        "help": "",
        "brief": "Responds to an open Ticket.",
        "usage": "<ticket ID>",
        "aliases": [],
        "extras": {"Category": "Dev"}
    }

    @commands.command(
            name = "ticketrespond",
            help = Help["help"],
            brief = Help["brief"],
            usage = Help["usage"],
            aliases = Help["aliases"],
            hidden = True,
            extras = Help["extras"]
    )
    async def ticketrespond(self, ctx: commands.Context[commands.Bot], ticketId: int | str | None):
        #if user already has an active session
        if ctx.author.id in sessions:
            return await ctx.reply("You already have an open responding session. Try closing that one and try again.")
        
        #if user doesn't enter the ticket id
        if not ticketId:
            return await ctx.reply("You must enter a Ticket ID to respond.")
        
        #if user enters an invalid ticket id
        if not isinstance(ticketId, int):
            raise commands.BadArgument
        
        conn = await connection() #makes a connection to the database
        conn.row_factory = aiosqlite.Row

        #fetches the ticket
        async with conn.execute("""
        SELECT user_id, message_collector_id, subject FROM tickets
        WHERE id = ?;
        """, (ticketId,)) as cursor:
            row = await cursor.fetchone()
        #if no ticket with given id found
        if not row:
            return await ctx.reply("No Ticket with given ID found.")
        
        sessions[ctx.author.id] = [] #creates a session for the admin
        
        #fetches the ticket user
        try:
            user = self.bot.get_user(row["user_id"]) or await self.bot.fetch_user(row["user_id"])
        except discord.NotFound :
            return await ctx.reply("The user who opened this Ticket doesn't exist anymore.")
        
        channel = user.dm_channel or await user.create_dm() #fetches the dm of the ticket user

        #fetches the message collecter message
        try:
            messageCollector = await channel.fetch_message(row["message_collector_id"])
        except discord.NotFound:
            messageCollector = None

        view = TicketView(ctx, conn, ticketId, user, channel, messageCollector, row["subject"]) #initializes the Ticket View
        await view.start() #starts the view

    @ticketrespond.error
    async def ticket_error(self, ctx: commands.Context[commands.Bot], error: commands.CommandError):
        #if user entered an invalid argument
        if isinstance(error, commands.BadArgument):
            await ctx.reply("Enter a valid Ticket ID.")
        else:
            logger.exception(f"❌ something went wrong with ticketrespond command:")
            await ctx.reply("something went wrong with **ticketrespond**.")

    #ticket slash command
    @app_commands.command(
        name = "ticketrespond",
        description = Help["brief"],
        extras = Help["extras"]
    )
    @app_commands.dm_only()
    async def slashTicketrespond(self, interaction: discord.Interaction, ticketId: int):
        #if user already has an active session
        if interaction.user.id in sessions:
            return await interaction.response.send_message("You already have an open responding session. Try closing that one and try again.", ephemeral = True)
        
        conn = await connection() #makes a connection to the database
        conn.row_factory = aiosqlite.Row

        #fetches the ticket
        async with conn.execute("""
        SELECT user_id, message_collector_id, subject FROM tickets
        WHERE id = ?;
        """, (ticketId,)) as cursor:
            row = await cursor.fetchone()
        #if no ticket with given id found
        if not row:
            return await interaction.response.send_message("No Ticket with given ID found.", ephemeral = True)
        
        sessions[interaction.user.id] = [] #creates a session for the admin
        
        #fetches the ticket user
        try:
            user = self.bot.get_user(row["user_id"]) or await self.bot.fetch_user(row["user_id"])
        except discord.NotFound :
            return await interaction.response.send_message("The user who opened this Ticket doesn't exist anymore.", ephemeral = True)
        
        channel = user.dm_channel #fetches the dm of the ticket user

        #fetches the message collecter message
        try:
            messageCollector = await channel.fetch_message(row["message_collector_id"]) if channel else None
        except discord.NotFound:
            messageCollector = None

        view = TicketView(interaction, conn, ticketId, user, messageCollector, row["subject"]) #initializes the Ticket View
        await view.start() #starts the view

    @slashTicketrespond.error
    async def slashTicketrespond_error(self, interaction: discord.Interaction, error: Exception):
        logger.exception(f"❌ something went wrong with /ticketrespond command:")
        try:
            await interaction.response.send_message("something went wrong with **ticketrespond**.", ephemeral = True)
        except discord.InteractionResponded:
            await interaction.followup.send("something went wrong with **ticketrespond**.", ephemeral = True)

    #the message collecter listener
    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return
        
        if msg.author.id in sessions:
            sessions[msg.author.id].append(msg)

class TicketView(discord.ui.View):
    def __init__(self, ctx: commands.Context[commands.Bot] | discord.Interaction, conn: aiosqlite.Connection, ticketId: int, ticketUser: discord.User, messageCollector: discord.Message | None, subject: str):
        super().__init__(timeout = 300)
        if isinstance(ctx, discord.Interaction):
            self.slash = True
            self.interaction = ctx
            self.user = ctx.user
        else:
            self.slash = False
            self.ctx = ctx
            self.user = ctx.author
        self.conn = conn
        self.ticketId = ticketId
        self.ticketUser = ticketUser
        self.messageCollector = messageCollector
        self.subject = subject
        self.timestamp = discord.utils.utcnow()

    async def start(self):
        initialEmbed = discord.Embed(
            title = "Ticket Response 🎫",
            description = (
                f"You have opened a **Ticket respond** Session."
                "\nSend as many messages as you want to resspond and hit `done` to close the interaction."
            ),
            color = discord.Color.blurple(),
            timestamp = self.timestamp
        )
        if self.slash:
            await self.interaction.response.send_message(embed = initialEmbed, view = self)
        else:
            self.msg = await self.ctx.reply(embed = initialEmbed, view = self)

    #done button
    @discord.ui.button(
        label = "done",
        style = discord.ButtonStyle.green,
        row = 0
    )
    async def done(self, interaction: discord.Interaction, button: discord.ui.Button[discord.ui.View]):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("You can't control this session.", ephemeral = True)
        
        messages = sessions.pop(self.user.id) #ends the user session and collects the sent messages

        #if no message is sent, session gets canceled
        if not messages:
            endEmbed = discord.Embed(
                title = "Ticket Response 🎫",
                description = "You sent no messages, session ended.",
                color = discord.Color.dark_gray(),
                timestamp = self.timestamp
            )
            if self.slash:
                await self.interaction.edit_original_response(embed = endEmbed, view = None)
            else:
                await self.msg.edit(embed = endEmbed, view = None)
                
            return self.stop()
        
        desc = (
            f"{self.ticketUser.mention}, An Admin has sent you a response for [this]({self.messageCollector.jump_url}) Ticket with subject: **\"{self.subject}\"**."
            if self.messageCollector else
            f"{self.ticketUser.mention}, An Admin has sent you a response for your Ticket with subject: **\"{self.subject}\"**."
        )
        sendingEmbed = discord.Embed(
            title = "Ticket Response !🎫",
            description = desc,
            color = discord.Color.blurple(),
            timestamp = self.timestamp
        )
        msg = await self.messageCollector.reply(embed = sendingEmbed) if self.messageCollector else await self.ticketUser.send(embed = sendingEmbed) #sends the initial message to the ticket user

        #replys the collected messages to the initial message
        for m in messages:
            #if message is sticker
            if m.stickers:
                for s in m.stickers:
                    await msg.reply(s.url)
                break

            #if message is text, file or embed or combinations of them
            content = m.content
            files = [await a.to_file() for a in m.attachments]

            await msg.reply(content = content, files = files, embeds = m.embeds)

        #updates the state of the ticket
        await self.conn.execute("""
        UPDATE tickets
        SET state = ?, closed_at = ?
        WHERE id = ?;
        """, ("closed", self.timestamp, self.ticketId))
        await self.conn.commit()

        await self.conn.close()

        #sends the succeed message to the admin
        notifyEmbed = discord.Embed(
            title = "Ticket Response 🎫",
            description = f"Your Response to the Ticket with ID **{self.ticketId}** has been sent succesfully.",
            color = discord.Color.green(),
            timestamp = self.timestamp
        )
        if self.slash:
            await self.interaction.edit_original_response(embed = notifyEmbed, view = None)
        else:
            await self.msg.edit(embed = notifyEmbed, view = None)
        
        self.stop()

    #cancel button
    @discord.ui.button(
            label = "cancel",
            style = discord.ButtonStyle.gray,
            row = 0
    )
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button[discord.ui.View]):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("You can't control this session.", ephemeral = True)
        
        sessions.pop(self.user.id, None) #ends the session

        #sends the cancel message to the user
        endEmbed = discord.Embed(
            title = "Ticket Response 🎫",
            description = "You canceled the session.",
            color = discord.Color.dark_gray(),
            timestamp = self.timestamp
        )
        if self.slash:
            await self.interaction.edit_original_response(embed = endEmbed, view = None)
        else:
            await self.msg.edit(embed = endEmbed, view = None)
    
        self.stop()

    async def on_timeout(self):
        #disables buttons on timeout
        for btn in self.children:
            if isinstance(btn, discord.ui.Button):
                btn.disabled = True

        sessions.pop(self.user.id, None) #ends the session

        #sends the timeout message
        toEmbed = discord.Embed(
            title = "Ticket Response 🎫",
            description = f"⏰ Ticket Response session timeout.",
            color = discord.Color.dark_gray(),
            timestamp = self.timestamp
        )
        try:
            if self.slash:
                await self.interaction.edit_original_response(embed = toEmbed, view = self)
            else:
                await self.msg.edit(embed = toEmbed, view = self)
        except discord.NotFound:
            pass

        self.stop() #stops the interaction upon timeout

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item[discord.ui.View]):
        logger.exception(f"❌ something went wrong with ticketrespond interaction - button: {getattr(item, 'label', 'unknown')}")
        try:
            await interaction.response.send_message("something went wrong with **ticketrespond**.", ephemeral = True)
        except discord.InteractionResponded:
            await interaction.followup.send("something went wrong with **ticketrespond**.", ephemeral = True)
        except Exception:
            pass
            
        self.stop() #stops the interaction upon error


async def setup(bot: commands.Bot):
    await bot.add_cog(TicketRespond(bot))