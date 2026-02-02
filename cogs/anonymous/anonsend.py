import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
from database import connection
from typing import TypedDict
from cogs.utility.help import HelpData
from cogs.anonymous.anonid import idGenerator, publicIdLength
from logHandler import loggerSetup

logger = loggerSetup(__name__)

privateIdLength = 6 #the length of the private ids

class sessionData(TypedDict):
    messages: list[discord.Message]
    reciever_id: int
sessions: dict[int, sessionData] = {}

async def privateIdGenerator(conn: aiosqlite.Connection, publicId: str):
    while True:
        privateId = idGenerator(privateIdLength)
        async with conn.execute("""
        SELECT 1 FROM anonusercontact
        WHERE public_id = ? AND sender_anon_id = ?;
        """, (publicId, privateId)) as cursor:
            found = await cursor.fetchone()
        if not found:
            return privateId

class AnonSend(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    Help: HelpData = {
        "help": (
            "Starts an anonymous messaging session, allowing the user to send as many messages as they want anonymously to the target who has shared their public ID."
        ),
        "brief": "Sends an anonymous message to someone.",
        "usage": "<public ID>",
        "aliases": ["anons"],
        "extras": {"Category": "Anonymous", "dm-only": "Yes"}
    }

    @commands.command(
            name = "anonsend",
            help = Help["help"],
            brief = Help["brief"],
            usage = Help["usage"],
            aliases = Help["aliases"],
            extras = Help["extras"]
    )
    async def anonsend(self, ctx: commands.Context[commands.Bot], publicId: str | None):
        #if user runs the command in a server
        if ctx.guild:
            return await ctx.reply("This command can only be used in Amélie's dm.")

        #if user already has an active session
        if ctx.author.id in sessions:
            return await ctx.reply("You are already in a messaging session, close the open one and try again.")
        
        #if user doesn't enter any id
        if not publicId:
            return await ctx.reply("You must enter the user's Public ID to send anonymous message to.")
        
        #if user enters an invalid id
        if len(publicId) != publicIdLength:
            return await ctx.reply("Enter a valid public ID.")
        
        conn = await connection() #makes a connection to the database
        conn.row_factory = aiosqlite.Row

        #checks if a user with given public id exists
        async with conn.execute("""
        SELECT user_id FROM anonpublicids
        WHERE public_id = ?;
        """, (publicId,)) as cursor:
            row = await cursor.fetchone()
        #if user with given public id doesn't exist
        if not row:
            return await ctx.reply("User with this ID doesn't exist.")
        
        recieverUser = self.bot.get_user(row["user_id"]) or await self.bot.fetch_user(row["user_id"]) #fetches the reciever user from found id
        
        #if user contact doesn't exist
        async with conn.execute("""
        SELECT sender_anon_id, blocked from anonusercontact
        WHERE public_id = ? AND sender_id = ?;
        """, (publicId, ctx.author.id)) as cursor:
            row = await cursor.fetchone()

        #if user is not in target user anon contact, creates the contact
        if not row:
            newId = await privateIdGenerator(conn, publicId)
            await conn.execute("""
            INSERT INTO anonusercontact (public_id, sender_id, sender_anon_id)
            VALUES (?, ?, ?);
            """, (publicId, ctx.author.id, newId))
            await conn.commit()
            privateId = newId

        #if user contact exists but is blocked
        elif row["blocked"] == 1:
            return await ctx.reply("You can't send anonymous messages to this user.")

        else:
            privateId: str = row["sender_anon_id"]

        #opens a session
        sessions[ctx.author.id] = {
            "messages": [],
            "reciever_id" : recieverUser.id
        }
        
        view = AnonView(ctx, conn, recieverUser, publicId, privateId, sessions) #initializes the Anon View
        await view.start()

    @anonsend.error
    async def anonsend_error(self, ctx: commands.Context[commands.Bot], error: Exception):
        logger.exception(f"❌ something went wrong with anonsend command:")
        await ctx.reply("something went wrong with **anonsend**.")

    #anonsend slash command
    @app_commands.command(
        name = "anonsend",
        description = Help["brief"],
        extras = Help["extras"]
    )
    @app_commands.dm_only()
    async def slashAnonsend(self, interaction: discord.Interaction, public_id: str):
        #if user already has an active session
        if interaction.user.id in sessions:
            return await interaction.response.send_message("You are already in a messaging session, close the open one and try again.", ephemeral = True)
        
        #if user enters an invalid id
        if len(public_id) != publicIdLength:
            return await interaction.response.send_message("Enter a valid ID.", ephemeral = True)
        
        conn = await connection() #makes a connection to the database
        conn.row_factory = aiosqlite.Row

        #checks if a user with given public id exists
        async with conn.execute("""
        SELECT user_id FROM anonpublicids
        WHERE public_id = ?;
        """, (public_id,)) as cursor:
            row = await cursor.fetchone()
        #if user with given public id doesn't exist
        if not row:
            return await interaction.response.send_message("User with this ID doesn't exist.", ephemeral = True)
        
        recieverUser = self.bot.get_user(row["user_id"]) or await self.bot.fetch_user(row["user_id"]) #fetches the reciever user from found id
        
        #if user contact doesn't exist
        async with conn.execute("""
        SELECT sender_anon_id, blocked from anonusercontact
        WHERE public_id = ? AND sender_id = ?;
        """, (public_id, interaction.user.id)) as cursor:
            row = await cursor.fetchone()

        #if user is not in target user anon contact, creates the contact
        if not row:
            newId = await privateIdGenerator(conn, public_id)
            await conn.execute("""
            INSERT INTO anonusercontact (public_id, sender_id, sender_anon_id)
            VALUES (?, ?, ?);
            """, (public_id, interaction.user.id, newId))
            await conn.commit()
            privateId = newId

        #if user contact exists but is blocked
        elif row["blocked"] == 1:
            return await interaction.response.send_message("You can't send anonymous messages to this user.", ephemeral = True)
        
        else:
            privateId: str = row["sender_anon_id"]

        #opens a session
        sessions[interaction.user.id] = {
            "messages": [],
            "reciever_id" : recieverUser.id
        }
        
        view = AnonView(interaction, conn, recieverUser, public_id, privateId, sessions) #initializes the Anon View
        await view.start() #starts the view

    @slashAnonsend.error
    async def slashAnonsend_error(self, interaction: discord.Interaction, error: Exception):
        logger.exception(f"❌ something went wrong with /Anonsend command:")
        try:
            await interaction.response.send_message("something went wrong with **Anonsend**.", ephemeral = True)
        except discord.InteractionResponded:
            await interaction.followup.send("something went wrong with **Anonsend**.", ephemeral = True)

    #the message collecter listener
    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return
        if msg.guild:
            return
        
        if msg.author.id in sessions:
            sessions[msg.author.id]["messages"].append(msg)

class AnonView(discord.ui.View):
    def __init__(self, ctx: commands.Context[commands.Bot] | discord.Interaction, conn: aiosqlite.Connection, recieverUser: discord.User, public_id: str, private_id: str, sessions: dict[int, sessionData]):
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
        self.recieverUser = recieverUser
        self.public_id = public_id
        self.private_id = private_id
        self.sessions = sessions

    async def start(self):
        initialEmbed = discord.Embed(
                title = "Anonymous Message",
                description = (
                    f"You are texting `{self.recieverUser.display_name}` anonymously."
                    "\nSend as many messages as you want and hit `done` to close the interaction."
                ),
                color = discord.Color.blurple()
            )
        #sends the initial message and stores channel and message id
        if not self.slash:
            self.msg = await self.ctx.reply(embed = initialEmbed, view = self)
            self.msgId = self.msg.id
        else:
            await self.interaction.response.send_message(embed = initialEmbed, view = self)
            msg = await self.interaction.original_response()
            self.msgId = msg.id
        
    #done button
    @discord.ui.button(
        label = "done",
        style = discord.ButtonStyle.green,
        row = 0
    )
    async def done(self, interaction: discord.Interaction, button: discord.ui.Button[discord.ui.View]):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("You can't control this session.", ephemeral = True)
        
        await interaction.response.defer()

        now = discord.utils.utcnow()
        
        endedSession = self.sessions.pop(self.user.id) #ends the session
        messages = endedSession["messages"] #collects the messages

        #if no message is sent, session gets canceled
        if not messages:
            endEmbed = discord.Embed(
                title = "Anonymous Message",
                description = "You sent no message, session ended.",
                color = discord.Color.dark_gray(),
                timestamp = now
            )
            if not self.slash:
                await self.msg.edit(embed = endEmbed, view = None)
            else:
                await self.interaction.edit_original_response(embed = endEmbed, view = None)
        
            self.stop()
            return

        #creates the session id
        async with self.conn.execute("""
        SELECT COALESCE(MAX(session_id), 0) + 1
        FROM anonsessions
        WHERE reciever_id = ? AND sender_id = ?;
        """, (self.public_id, self.private_id)) as cursor:
            row = await cursor.fetchone()
        sessionId: int = row[0] if row else 1

        #stores the session in the database
        await self.conn.execute("""
        INSERT INTO anonsessions (session_id, reciever_id, sender_id, sender_message_collector_id, session_date)
        VALUES (?, ?, ?, ?, ?);
        """, (sessionId, self.public_id, self.private_id, self.msgId, now))
        await self.conn.commit()

        await self.conn.close()

        #send the messages to the target
        sendingEmbed = discord.Embed(
            title = "new Anonymous Message !",
            description = (
                f"User with ID: `{self.private_id}` (Session ID: *{sessionId}*) has sent you these messages:"
            ),
            color = discord.Color.blurple(),
            timestamp = now
        )
        msg = await self.recieverUser.send(embed = sendingEmbed) #sends an initial message to the reciever

        #replys the collected messages
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
            title = "Anonymous Message",
            description = f"Your messages have been sent to `{self.recieverUser.name}` succesfully. (Session ID: *{sessionId}*)",
            color = discord.Color.green(),
            timestamp = now
        )
        if not self.slash and isinstance(self.msg, discord.Message):
            await self.msg.edit(embed = notifyEmbed, view = None)
        else:
            await self.interaction.edit_original_response(embed = notifyEmbed, view = None)
        
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
        
        await interaction.response.defer()

        now = discord.utils.utcnow()
        
        self.sessions.pop(self.user.id) #ends the session

        #sends the cancel message to the user
        endEmbed = discord.Embed(
                title = "Anonymous Message",
                description = "You canceled the session.",
                color = discord.Color.dark_gray(),
                timestamp = now
            )
        if not self.slash:
            await self.msg.edit(embed = endEmbed, view = None)
        else:
            await self.interaction.edit_original_response(embed = endEmbed, view = None)
    
        self.stop()

    async def on_timeout(self):
        #disables buttons on timeout
        for btn in self.children:
            if isinstance(btn, discord.ui.Button):
                btn.disabled = True

        self.sessions.pop(self.user.id) #ends the session

        #sends the timeout message
        toEmbed = discord.Embed(
            title = "Anonymous Message",
            description = f"⏰ Session timeout."
        )
        try:
            if not self.slash and isinstance(self.msg, discord.Message):
                await self.msg.edit(embed = toEmbed, view = self)
            else:
                await self.interaction.edit_original_response(embed = toEmbed, view = self)
        except discord.NotFound:
            pass

        self.stop()

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item[discord.ui.View]):
        logger.exception(f"❌ something went wrong with anonsend interaction - button: {getattr(item, 'label', 'unknown')}")
        try:
            await interaction.response.send_message("something went wrong with **anonsend**.", ephemeral = True)
        except discord.InteractionResponded:
            await interaction.followup.send("something went wrong with **anonsend**.", ephemeral = True)
        except Exception:
            pass
            
        self.stop()
        

async def setup(bot: commands.Bot):
    await bot.add_cog(AnonSend(bot))