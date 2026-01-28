import discord
from discord.ext import commands
from discord import app_commands
import json
from database import connection
from cogs.utility.help import HelpData
from logHandler import loggerSetup

logger = loggerSetup(__name__)

with open("config.json") as file:
    config = json.load(file)
TicketPlaceId = config["ADMINS"][0] #where tickets should be sent, either admins' dm or a channel

sessions: dict[int, list[discord.Message]] = {}

class Ticket(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    Help: HelpData = {
        "help": (
            "Opens a ticketing session to contact the staff."
            "\n\nPlease try to include a short subject, a clear description of the issue,"
            " when it happened, and any relevant screenshots or files."
            "\nYou may send multiple messages during the session."
            " Press **done** when finished to submit the ticket."
            "\n\nYour username and user ID will be included automatically for follow-up."
        ),
        "brief": "Opens a support ticket.",
        "usage": "",
        "aliases": [],
        "extras": {"Category": "Utility", "dm-only": "Yes"}
    }

    @commands.command(
            name = "ticket",
            help = Help["help"],
            brief = Help["brief"],
            usage = Help["usage"],
            aliases = Help["aliases"],
            extras = Help["extras"]
    )
    async def ticket(self, ctx: commands.Context[commands.Bot], subject: str | None):
        #if user runs the command in a server
        if ctx.guild:
            return await ctx.reply("This command can only be used in Amélie's dm.")
        
        #if user already has an active session
        if ctx.author.id in sessions:
            return await ctx.reply("You already have an open Ticketing session, try closing that one and try again.")
        
        #if user doesn't enter the ticket subject
        if not subject:
            return await ctx.reply("You must enter a subject to open the Ticket.")
        
        sessions[ctx.author.id] = [] #creates a session for the user

        admin = self.bot.get_user(TicketPlaceId) or await self.bot.fetch_user(TicketPlaceId) #fetches the admin user to send the message to

        view = TicketView(ctx, subject, admin) #initializes the Ticket View
        await view.start() #starts the view

    @ticket.error
    async def ticket_error(self, ctx: commands.Context[commands.Bot], error: commands.CommandError):
        logger.exception(f"❌ something went wrong with ticket command:")
        await ctx.reply("something went wrong with **ticket**.")

    #ticket slash command
    @app_commands.command(
        name = "ticket",
        description = Help["brief"],
        extras = Help["extras"]
    )
    @app_commands.dm_only()
    async def slashTicket(self, interaction: discord.Interaction, subject: str):
        #if user already has an active session
        if interaction.user.id in sessions:
            return await interaction.response.send_message("You already have an open Ticketing session, try closing that one and try again.", ephemeral = True)
        
        sessions[interaction.user.id] = [] #creates a session for the user

        admin = self.bot.get_user(TicketPlaceId) or await self.bot.fetch_user(TicketPlaceId) #fetches the admin user to send the message to

        view = TicketView(interaction, subject, admin) #initializes the Ticket View
        await view.start() #starts the view

    @slashTicket.error
    async def slashTicket_error(self, interaction: discord.Interaction, error: Exception):
        logger.exception(f"❌ something went wrong with /ticket command:")
        try:
            await interaction.response.send_message("something went wrong with **ticket**.", ephemeral = True)
        except discord.InteractionResponded:
            await interaction.followup.send("something went wrong with **ticket**.", ephemeral = True)

    #the message collecter listener
    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return
        if msg.guild:
            return
        
        if msg.author.id in sessions:
            sessions[msg.author.id].append(msg)

class TicketView(discord.ui.View):
    def __init__(self, ctx: commands.Context[commands.Bot] | discord.Interaction, subject: str, admin: discord.User):
        super().__init__(timeout = 300)
        if isinstance(ctx, discord.Interaction):
            self.slash = True
            self.interaction = ctx
            self.user = ctx.user
        else:
            self.slash = False
            self.ctx = ctx
            self.user = ctx.author
        self.subject = subject
        self.admin = admin
        self.timestamp = discord.utils.utcnow()

    async def start(self):
        initialEmbed = discord.Embed(
            title = "Ticket 🎫",
            description = (
                f"You have opened a **Ticketing** Session."
                "\nSend as many messages as you want and hit `done` to close the interaction."
                "\n\n**note: Your *username* and *ID* will be included in the Ticket for more contact.**"
            ),
            color = discord.Color.blurple(),
            timestamp = self.timestamp
        )
        if self.slash:
            await self.interaction.response.send_message(embed = initialEmbed, view = self)
            msg = await self.interaction.original_response()
            self.collectorId = msg.id #stores the collector message id
        else:
            self.msg = await self.ctx.reply(embed = initialEmbed, view = self)
            self.collectorId = self.msg.id #stores the collector message id

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
                title = "Ticket 🎫",
                description = "You sent no messages, session ended.",
                color = discord.Color.dark_gray(),
                timestamp = self.timestamp
            )
            if self.slash:
                await self.interaction.edit_original_response(embed = endEmbed, view = None)
            else:
                await self.msg.edit(embed = endEmbed, view = None)
                
            self.stop()
            return
        
        conn = await connection() #makes a connection to the database

        #creates a ticket in the database for later response
        cursor = await conn.execute("""
        INSERT INTO tickets (user_id, message_collector_id, subject, created_date)
        VALUES (?, ?, ?, ?);
        """, (self.user.id, self.collectorId, self.subject, self.timestamp))
        await conn.commit()
        ticketId = cursor.lastrowid #fetches the created ticket id
        await conn.close()
        
        #sends the ticket
        sendingEmbed = discord.Embed(
            title = "new Ticket !🎫",
            description = (
                f"{self.user.mention} with ID {self.user.id} has sent a Ticket."
            ),
            color = discord.Color.blurple(),
            timestamp = self.timestamp
        ).set_footer(text = f"Ticket No. {ticketId}")
        msg = await self.admin.send(embed = sendingEmbed) #sends an initial message to the reciever

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

        #sends the succeed message to the user
        notifyEmbed = discord.Embed(
            title = "Ticket 🎫",
            description = f"Your Ticket has been sent succesfully.",
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
            title = "Ticket 🎫",
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
            title = "Ticket 🎫",
            description = f"⏰ Ticket session timeout.",
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
        logger.exception(f"❌ something went wrong with ticket interaction - button: {getattr(item, 'label', 'unknown')}")
        try:
            await interaction.response.send_message("something went wrong with **ticket**.", ephemeral = True)
        except discord.InteractionResponded:
            await interaction.followup.send("something went wrong with **ticket**.", ephemeral = True)
        except Exception:
            pass
            
        self.stop() #stops the interaction upon error


async def setup(bot: commands.Bot):
    await bot.add_cog(Ticket(bot))