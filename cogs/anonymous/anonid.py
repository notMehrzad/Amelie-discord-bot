import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
from database import connection
import secrets
import string
from logHandler import loggerSetup

logger = loggerSetup(__name__)

publicIdLength = 12 #the length of the public ids

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

class AnonId(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name = "anonid",
        aliases = ["anonymousid"],
        brief = "Shows the anonymous ID for the user.",
        help = "",
        extras = {"Category": "Anonymous", "dm-only": "Yes"}
    )
    async def anonid(self, ctx: commands.Context[commands.Bot]):
        #if user runs teh command in a server
        if ctx.guild:
            return await ctx.reply("This command can only be used in Amélie's dm.")

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

    @anonid.error
    async def anonid_error(self, ctx: commands.Context[commands.Bot], error: Exception):
        logger.exception(f"❌ something went wrong with anonid command:")
        await ctx.reply("something went wrong with **anonid**.")

    #anonid slash command
    @app_commands.command(
        name = "anonid",
        description = "Shows the anonymous ID for the user.",
         extras = {"Category": "Anonymous", "dm-only": "Yes"}
    )
    @app_commands.dm_only()
    async def slashAnonid(self, interaction: discord.Interaction):
        await interaction.response.defer()

        conn = await connection() #makes a connection to the database

        #checks if the user id exists or not
        async with conn.execute("""
        SELECT public_id FROM anonpublicids
        WHERE user_id = ?;
        """, (interaction.user.id,)) as cursor:
            row = await cursor.fetchone()

        #if user id doesn't exist
        if not row:
            newId = await publicId(conn) #creates an id
            
            #inserts the new created id
            await conn.execute("""
            INSERT INTO anonpublicids (public_id, user_id, created_date)
            VALUES (?, ?, ?)
            """, (newId, interaction.user.id, discord.utils.utcnow()))
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
            """, (newId, interaction.user.id))
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
        await interaction.followup.send(embed = resultEmbed) #sends the result

    @slashAnonid.error
    async def slashAnonid_error(self, interaction: discord.Interaction, error: Exception):
        logger.exception(f"❌ something went wrong with /anonid command:")
        try:
            await interaction.response.send_message("something went wrong with **anonid**.", ephemeral = True)
        except discord.InteractionResponded:
            await interaction.followup.send("something went wrong with **anonid**.", ephemeral = True)
        

async def setup(bot: commands.Bot):
    await bot.add_cog(AnonId(bot))