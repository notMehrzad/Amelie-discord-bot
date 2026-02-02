import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
from database import connection
from cogs.anonymous.anonsend import privateIdLength
from cogs.utility.help import HelpData
from logHandler import loggerSetup

logger = loggerSetup(__name__)

class AnonReply(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    Help: HelpData = {
        "help": (
            "Replys to an anonymous session created via the anonymous sender."
            "\nThe anonymous sender will recieve the reply message and get notified who responded to their anonymous session."
        ),
        "brief": "Replys to an anonymous session.",
        "usage": "<private ID> <session ID> <message>",
        "aliases": ["anonr"],
        "extras": {"Category": "Anonymous", "dm-only": "Yes"}
    }

    @commands.command(
            name = "anonreply",
            help = Help["help"],
            brief = Help["brief"],
            usage = Help["usage"],
            aliases = Help["aliases"],
            extras = Help["extras"]
    )
    async def anonreply(self, ctx: commands.Context[commands.Bot], privateId: str | None, sessionId: int | str | None, *, message: str | None):
        #if user runs the command in a server
        if ctx.guild:
            return await ctx.reply("This command can only be used in Amélie's dm.")
        
        conn = await connection() #makes a connection to the database
        conn.row_factory = aiosqlite.Row

        #checks if user has a public id
        async with conn.execute("""
        SELECT public_id FROM anonpublicids
        WHERE user_id = ?;
        """, (ctx.author.id,)) as cursor:
            row = await cursor.fetchone()
        if not row:
            return await ctx.reply("You have no public ID so nobody has sent you anything.")

        public_id: str = row["public_id"]
        
        #if user doesn't enter target private id
        if not privateId:
            return await ctx.reply("You must enter the private ID of the user you want to reply.")
        
        if len(privateId) != privateIdLength:
            return await ctx.reply("Enter a valid private ID.")
        
        #checks if target private id is in users anon contact
        async with conn.execute("""
        SELECT sender_id, blocked FROM anonusercontact
        WHERE public_id = ? AND sender_anon_id = ?;
        """, (public_id, privateId)) as cursor:
            row = await cursor.fetchone()
        if not row:
            return await ctx.reply("User with given ID hasn't sent you anything.")
        
        if row["blocked"]:
            return await ctx.reply("You have blocked this user and can't reply to them anymore.")
        
        senderUserId: int = row["sender_id"]
        try:
            senderUser = self.bot.get_user(senderUserId) or await self.bot.fetch_user(senderUserId) #fetchs the sender user

        #if user doesn't exist anymore, deletes the contact
        except discord.NotFound:
            await conn.execute("""
            DELETE FROM anonusercontact
            WHERE public_id = ? AND sender_id = ?;
            """, (public_id, senderUserId))
            await conn.commit()

            return await ctx.reply("The sender with this private ID doesn't exist anymore.")
        
        #if user doesn't enter the session id
        if not sessionId:
            return await ctx.reply("You must enter the session ID you want to reply.")
        #if user doesn't enter a valid session id
        if not isinstance(sessionId, int):
            return await ctx.reply("Enter a valid session ID.")
        
        #checks if session id with target private id exists in sessions
        async with conn.execute("""
        SELECT sender_message_collector_id, responded FROM anonsessions
        WHERE reciever_id = ? AND sender_id = ? AND session_id = ?;
        """, (public_id, privateId, sessionId)) as cursor:
            row = await cursor.fetchone()
        if not row:
            return await ctx.reply("User with given ID had no such session with you.")
        
        if row["responded"] == 1:
            return await ctx.reply("You have already responded this session before.")
        
        channel = senderUser.dm_channel #fetches the dm channel
        #fetches the message collecter message
        try:
            messageCollector = await channel.fetch_message(row["sender_message_collector_id"]) if channel else None
        except discord.NotFound:
            messageCollector = None

        #if user doesn't enter message
        if not message:
            return await ctx.reply("You must enter your message to be replied to this session.")
        
        now = discord.utils.utcnow()
        
        desc = (
            f"`{ctx.author.display_name}` has replied to [this]({messageCollector.jump_url}) Session(Session ID: *{sessionId}*):"
            if messageCollector else
            f"`{ctx.author.display_name}` has replied to the Session(Session ID: *{sessionId}*):"
        )
        sendingEmbed = discord.Embed(
            title = "Anonymous Message",
            description = desc,
            color = discord.Color.blurple(),
            timestamp = now
        )
        #sends and then replys to the initial notification message
        if messageCollector:
            msg = await messageCollector.reply(embed = sendingEmbed)
            await msg.reply(message)
        else:
            msg = await senderUser.send(embed = sendingEmbed)
            await msg.reply(message)
        
        #updates session status to responded
        await conn.execute("""
        UPDATE anonsessions
        SET responded = ?
        WHERE reciever_id = ? AND sender_id = ? AND session_id = ?;
        """, (1, public_id, privateId, sessionId))
        await conn.commit()

        await conn.close()

        resultEmbed = discord.Embed(
            title = "Anonymous Message",
            description = f"Your reply message for `{privateId}` with Session(Session ID: *{sessionId}*) has been sent.",
            color = discord.Color.green(),
            timestamp = now
        )
        await ctx.reply(embed = resultEmbed) #sends the succeed message for the user

    @anonreply.error
    async def anonreply_error(self, ctx: commands.Context[commands.Bot], error: Exception):
        logger.exception(f"❌ something went wrong with anonreply command:")
        await ctx.reply("something went wrong with **anonreply**.")

    #anonreply slash command
    @app_commands.command(
        name = "anonreply",
        description = Help["brief"],
        extras = Help["extras"]
    )
    @app_commands.dm_only()
    async def slashAnonreply(self, interaction: discord.Interaction, private_id: str, session_id: int, message: str):
        conn = await connection() #makes a connection to the database
        conn.row_factory = aiosqlite.Row

        #checks if user has a public id
        async with conn.execute("""
        SELECT public_id FROM anonpublicids
        WHERE user_id = ?;
        """, (interaction.user.id,)) as cursor:
            row = await cursor.fetchone()
        if not row:
            return await interaction.response.send_message("You have no public ID so nobody has sent you anything.", ephemeral = True)

        public_id: str = row["public_id"]

        if len(private_id) != privateIdLength:
            return await interaction.response.send_message("Enter a valid private ID.", ephemeral = True)
        
        #checks if target private id is in users anon contact
        async with conn.execute("""
        SELECT sender_id, blocked FROM anonusercontact
        WHERE public_id = ? AND sender_anon_id = ?;
        """, (public_id, private_id)) as cursor:
            row = await cursor.fetchone()
        if not row:
            return await interaction.response.send_message("User with given ID hasn't sent you anything.", ephemeral = True)
        
        if row["blocked"]:
            return await interaction.response.send_message("You have blocked this user and can't reply to them anymore.", ephemeral = True)
        
        senderUserId: int = row["sender_id"]
        try:
            senderUser = self.bot.get_user(senderUserId) or await self.bot.fetch_user(senderUserId) #fetchs the sender user

        #if user doesn't exist anymore, deletes the contact
        except discord.NotFound:
            await conn.execute("""
            DELETE FROM anonusercontact
            WHERE public_id = ? AND sender_id = ?;
            """, (public_id, senderUserId))
            await conn.commit()

            return await interaction.response.send_message("The sender with this private ID dosn't exist anymore.", ephemeral = True)

        #checks if session id with target private id exists in sessions
        async with conn.execute("""
        SELECT sender_message_collector_id, responded FROM anonsessions
        WHERE reciever_id = ? AND sender_id = ? AND session_id = ?;
        """, (public_id, private_id, session_id)) as cursor:
            row = await cursor.fetchone()
        if not row:
            return await interaction.response.send_message("User with given ID had no such session with you.", ephemeral = True)
        
        if row["responded"] == 1:
            return await interaction.response.send_message("You have already responded this session before.", ephemeral = True)
        
        channel = senderUser.dm_channel #fetches the dm channel
        #fetches the message collector message
        try:
            messageCollector = await channel.fetch_message(row["sender_message_collector_id"]) if channel else None
        except discord.NotFound:
            messageCollector = None
        
        now = discord.utils.utcnow()
        
        desc = (
            f"`{interaction.user.display_name}` has replied to [this]({messageCollector.jump_url}) Session(Session ID: *{session_id}*):"
            if messageCollector else
            f"`{interaction.user.display_name}` has replied to the Session(Session ID: *{session_id}*):"
        )
        sendingEmbed = discord.Embed(
            title = "Anonymous Message",
            description = desc,
            color = discord.Color.blurple(),
            timestamp = now
        )
        #sends and then replys to the initial notification message
        if messageCollector:
            msg = await messageCollector.reply(embed = sendingEmbed)
            await msg.reply(message)
        else:
            msg = await senderUser.send(embed = sendingEmbed)
            await msg.reply(message)

        #updates session status to responded
        await conn.execute("""
        UPDATE anonsessions
        SET responded = ?
        WHERE reciever_id = ? AND sender_id = ? AND session_id = ?;
        """, (1, public_id, private_id, session_id))
        await conn.commit()

        await conn.close()

        resultEmbed = discord.Embed(
            title = "Anonymous Message",
            description = f"Your reply message for `{private_id}` with Session(Session ID: *{session_id}*) has been sent.",
            color = discord.Color.green(),
            timestamp = now
        )
        await interaction.response.send_message(embed = resultEmbed) #sends the succeed message for the user

    @slashAnonreply.error
    async def slashAnonreply_error(self, interaction: discord.Interaction, error: Exception):
        logger.exception(f"❌ something went wrong with /anonreply command:")
        try:
            await interaction.response.send_message("something went wrong with **anonreply**.", ephemeral = True)
        except discord.InteractionResponded:
            await interaction.followup.send("something went wrong with **anonreply**.", ephemeral = True)
        

async def setup(bot: commands.Bot):
    await bot.add_cog(AnonReply(bot))