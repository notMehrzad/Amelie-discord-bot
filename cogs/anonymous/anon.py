import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
from database import connection
import secrets
import string
from typing import TypedDict
from logHandler import loggerSetup

logger = loggerSetup(__name__)

publicIdLength = 12 #the length of the public ids

class sessionData(TypedDict):
    messages: list[str]
    reciever_id: int

def idGenerator(length: int):
    characters = string.ascii_letters + string.digits
    return "".join(secrets.choice(characters) for _ in range(length))

async def publicId(conn: aiosqlite.Connection):
    while True:
        publicId = idGenerator(publicIdLength)
        async with conn.execute("""
        SELECT 1 FROM anonpublicids
        WHERE public_id = ?
        """, (publicId,)) as cursor:
            found = await cursor.fetchone()
        if not found:
            return publicId
async def privateId(conn: aiosqlite.Connection, publicId: str):
    while True:
        privateId = idGenerator(6)
        async with conn.execute("""
        SELECT 1 FROM anonusercontact
        WHERE public_id = ? AND sender_anon_id = ?;
        """, (publicId, privateId)) as cursor:
            found = await cursor.fetchone()
        if not found:
            return privateId

class Anon(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sessions: dict[int, sessionData] = {}

    @commands.command(
        name = "anon",
        aliases = ["anonymous"],
        brief = "Shows the anonymous ID for the user.",
        help = "",
        extras = {"Category": "Anonymous", "dm-only": "Yes"}
    )
    async def anon(self, ctx: commands.Context[commands.Bot], cmd: str | None, id: str | None):
        #if user runs teh command in a server
        if ctx.guild:
            return await ctx.reply("This command can only be used in Amélie's dm.")
        
        #if user doesn't enter any subcommand
        if not cmd:
            return await ctx.reply("You must enter a subcommand for this command. (try `/help anon`)")
        
        cmd = cmd.lower()
        #id subcommand
        if cmd == "id":
            conn = await connection() #makes a connection to the database

            #checks if the user id exists or not
            async with conn.execute("""
            SELECT public_id FROM anonpublicids
            WHERE user_id = ?;
            """, (ctx.author.id,)) as cursor:
                row = await cursor.fetchone()

            #if user id doesn't exist
            if not row:
                newId = await publicId(conn) #creates an id
                
                #inserts the new created id
                await conn.execute("""
                INSERT INTO anonpublicids (public_id, user_id, created_date)
                VALUES (?, ?, ?)
                """, (newId, ctx.author.id, discord.utils.utcnow()))
                await conn.commit()

                public_id = newId
            
            #checks if id length is ok
            elif len(row[0]) != publicIdLength:
                newId = await publicId(conn) #creates another id with updated length

                #updates the existing id
                await conn.execute("""
                UPDATE anonpublicids
                SET public_id = ?
                WHERE user_id = ?;
                """, (newId, ctx.author.id))
                await conn.commit()

                public_id = newId

            #public id exists
            else:
                public_id: str = row[0]
            
            await conn.close() #closes the connection

            resultEmbed = discord.Embed(
                title = "Anonymous ID",
                description = (
                    f"Your anonymous ID is: `{public_id}`"
                    "\nShare this somewhere and people can message you anonymously using `anonsend` command."
                ),
                color = discord.Color.blurple()
            )
            await ctx.reply(embed = resultEmbed) #sends the result
        
        #send subcommand
        elif cmd == "send":
            #if user already has an active session
            if ctx.author.id in self.sessions:
                return await ctx.reply("You are already in a messaging session, close the open one and try again.")
            
            #if user doesn't enter any id
            if not id:
                return await ctx.reply("You must enter the user ID you want to send anonymous message to.")
            
            #if user enters an invalid id
            if len(id) != publicIdLength:
                return await ctx.reply("Enter a valid ID.")
            
            conn = await connection() #makes a connection to the database
            conn.row_factory = aiosqlite.Row

            #checks if a user with given public id exists
            async with conn.execute("""
            SELECT user_id FROM anonpublicids
            WHERE public_id = ?;
            """, (id,)) as cursor:
                recieverId = await cursor.fetchone()
            #if user with given public id doesn't exist
            if not recieverId:
                return await ctx.reply("User with this ID doesn't exist.")
            
            recieverUser = self.bot.get_user(recieverId[0]) or await self.bot.fetch_user(recieverId[0]) #fetches the reciever user from found id
            
            #if user contact doesn't exist
            async with conn.execute("""
            SELECT sender_anon_id from anonusercontact
            WHERE public_id = ? AND sender_id = ?;
            """, (id, ctx.author.id)) as cursor:
                row = await cursor.fetchone()

            #if user is not in target user anon contact, creates the contact
            if not row:
                newAnonId = await privateId(conn, id)
                await conn.execute("""
                INSERT INTO anonusercontact (public_id, sender_id, sender_anon_id)
                VALUES (?, ?, ?);
                """, (id, ctx.author.id, newAnonId))
                await conn.commit()
                anonId = newAnonId

            #user anon contact exists
            else:
                anonId: str = row[0]

            await conn.close()

            #opens a session
            self.sessions[ctx.author.id] = {
                "messages": [],
                "reciever_id" : recieverUser.id
            }
            
            view = AnonView(ctx, recieverUser, anonId, self.sessions) #initializes the Anon View
            await view.start()

        #invalid subcommand
        else:
            return await ctx.reply("Enter a valid subcommand for this command. (try `/help anon`)")

    @anon.error
    async def anon_error(self, ctx: commands.Context[commands.Bot], error: Exception):
        logger.exception(f"❌ something went wrong with anon command:")
        await ctx.reply("something went wrong with **anon**.")

    #anon slash command
    @app_commands.command(
        name = "anon",
        description = "Shows the anonymous ID for the user.",
         extras = {"Category": "Anonymous", "dm-only": "Yes"}
    )
    @app_commands.dm_only()
    async def slashAnon(self, interaction: discord.Interaction):
        pass

    @slashAnon.error
    async def slashAnon_error(self, interaction: discord.Interaction, error: Exception):
        logger.exception(f"❌ something went wrong with /anon command:")
        try:
            await interaction.response.send_message("something went wrong with **anon**.", ephemeral = True)
        except discord.InteractionResponded:
            await interaction.followup.send("something went wrong with **anon**.", ephemeral = True)

    #the message collecter listener
    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return
        if msg.guild:
            return
        
        if msg.author.id in self.sessions:
            self.sessions[msg.author.id]["messages"].append(msg.content)

class AnonView(discord.ui.View):
    def __init__(self, ctx: commands.Context[commands.Bot] | discord.Interaction, recieverUser: discord.User, senderAnonId: str, sessions: dict[int, sessionData]):
        super().__init__(timeout = 300)
        if isinstance(ctx, discord.Interaction):
            self.slash = True
            self.interaction = ctx
        else:
            self.slash = False
            self.ctx = ctx
        self.user = self.ctx.author if not self.slash else self.interaction.user
        self.recieverUser = recieverUser
        self.senderAnonId = senderAnonId
        self.sessions = sessions

    async def start(self):
        initialEmbed = discord.Embed(
                title = "Anonymous Message",
                description = (
                    f"You are texting `{self.recieverUser.display_name}`."
                    "\nSend as many messages as you want and hit `done` to close the interaction."
                ),
                color = discord.Color.blurple(),
                timestamp = discord.utils.utcnow()
            )
        if not self.slash:
            self.msg = await self.ctx.reply(embed = initialEmbed, view = self)
        else:
            await self.interaction.response.send_message(embed = initialEmbed, view = self)
        
    #done button
    @discord.ui.button(
        label = "done",
        style = discord.ButtonStyle.green
    )
    async def done(self, interaction: discord.Interaction, button: discord.ui.Button[discord.ui.View]):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("You can't control this session.", ephemeral = True)
        
        await interaction.response.defer()
        
        endedSession = self.sessions.pop(self.user.id) #ends the session

        messages = endedSession["messages"] #collects the messages
        msg = await self.recieverUser.send(f"User with ID `{self.senderAnonId}` has sent you these messages:") #sends an initial message to the reciever
        #sends the collected messages
        for m in messages:
            await msg.reply(m)

        finalEmbed = discord.Embed(
            title = "Anonymous Message",
            description = f"Your messages have been sent to `{self.recieverUser.name}` succesfully.",
            color = discord.Color.blurple(),
            timestamp = discord.utils.utcnow()
        )
        if not self.slash:
            await self.msg.edit(embed = finalEmbed, view = None)
        else:
            await self.interaction.edit_original_response(embed = finalEmbed, view = None)
        
        self.stop()

    async def on_timeout(self):
        self.done.disabled = True

        toEmbed = discord.Embed(
            title = "Anonymous Message",
            description = f"⏰ Session timeout."
        )
        try:
            if not self.slash:
                await self.msg.edit(embed = toEmbed, view = self)
            else:
                await self.interaction.edit_original_response(embed = toEmbed, view = self)
        except discord.NotFound:
            pass

        self.stop()

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item[discord.ui.View]):
        logger.exception(f"❌ something went wrong with anon interaction - button: {getattr(item, 'label', 'unknown')}")
        try:
            await interaction.response.send_message("something went wrong with **anon**.", ephemeral = True)
        except discord.InteractionResponded:
            await interaction.followup.send("something went wrong with **anon**.", ephemeral = True)
        except Exception:
            pass
            
        self.stop() #stops further interaction
        

async def setup(bot: commands.Bot):
    await bot.add_cog(Anon(bot))