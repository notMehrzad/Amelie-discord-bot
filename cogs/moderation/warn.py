import discord
from discord.ext import commands
from discord import app_commands
from database import connection
from cogs.utility.help import HelpData
from logHandler import loggerSetup

logger = loggerSetup(__name__)

warnLimit = 3 #allowed number of warnings before getting kicked

class Warn(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    Help: HelpData = {
        "help": "",
        "brief": "Warns a member from the server.",
        "usage": "<target (mention *or* id)> <reason[*optional*]>",
        "aliases": ["w"],
        "extras": {"Category": "Moderation", "Permissions needed": "`Kick, Approve and Reject Members`", "server-only": "Yes"}
    }

    @commands.command(
            name = "warn",
            help = Help["help"],
            brief = Help["brief"],
            usage = Help["usage"],
            aliases = Help["aliases"],
            extras = Help["extras"]
    )
    async def warn(self, ctx: commands.Context[commands.Bot], user: discord.User | int | str | None, *, reason: str | None = None):
        #if user runs the command in dm
        if not ctx.guild or not isinstance(ctx.author, discord.Member):
            return await ctx.reply("You can only run moderation commands in a server.")
        
        #if the user has no permission to warn
        if not ctx.author.guild_permissions.kick_members:
            return await ctx.reply("You have no permission to *warn* Members.")
        
        #if the bot has no permission to warn
        if not ctx.guild.me.guild_permissions.kick_members:
            return await ctx.reply("I have no permisson to *warn* Members.")
        
        #if user didn't enter any target member
        if not user:
            return await ctx.reply("You must mention a target Member for this command.")
        
        #if user mentions an invalid user
        if not isinstance(user, (discord.abc.User, int)):
            raise commands.BadArgument
        
        try:
            user = (self.bot.get_user(user) or await self.bot.fetch_user(user)) if isinstance(user, int) else user #trys to fetch the target if id is given
        except discord.NotFound:
            return await ctx.reply(f"User with given ID doesn't exist.")
        
        target = ctx.guild.get_member(user.id) #fetches the target user from the server, None if not found
        if not target:
            return await ctx.reply(f"{user.display_name} is not a Member of this server.")
        
        #if user wants to warn himself
        if target.id == ctx.author.id:
            return await ctx.reply("You can't warn yourself!")
        
        #if user wants to warn the server owner
        if target.id == ctx.guild.owner_id:
            return await ctx.reply("You can't warn the server *Owner*.")
        
        #if user wants to run moderation command on the bot
        if target.id == ctx.me.id:
            return await ctx.reply("You can't run my moderation commands on myself darling.")
        
        #if user wants to warn bots
        if target.bot:
            return await ctx.reply("-agh seriously?. You can't warn bots.")
        
        #if user has lower or equal role position than target
        if target.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.reply("You can't warn a Member with *higher or equal* role position as you.")
        
        #if the bot has lower or equal role position than target
        if target.top_role >= ctx.guild.me.top_role:
            return await ctx.reply("I can't warn a Member with *higher or equal* role position as me.")
        
        #warns the target
        conn = await connection() #makes a connection to the database

        #creates the warn ID based on the last warn id
        async with conn.execute("""
        SELECT COALESCE(MAX(user_warn_id), 0) + 1
        FROM warns
        WHERE server_id = ? AND user_id = ?;
        """, (ctx.guild.id, target.id)) as cursor:
            result = await cursor.fetchone()
        warnID: int = result[0] if result else 1
            
        #inserts a new warn for given target
        await conn.execute("""
        INSERT INTO warns (server_id, user_warn_id, mod_id, user_id, reason, timestamp)
        VALUES (?, ?, ?, ?, ?, ?);
        """, (ctx.guild.id, warnID, ctx.author.id, target.id, reason, discord.utils.utcnow()))
        await conn.commit() #commits and saves the changes

        #counts the number of warns the target has
        async with conn.execute("""
        SELECT COUNT(*) FROM warns
        WHERE server_id = ? AND user_id = ?;
        """, (ctx.guild.id, target.id)) as cursor:
            result = await cursor.fetchone()
        warnCount: int = result[0] if result else 0

        await conn.close()

        await ctx.reply(f"{target.mention} has been warned." + (f"\nreason: {reason}" if reason else ""))

        #if the target has over alowed number of warns, kicks it
        if warnCount >= warnLimit:
            try:
                await ctx.guild.kick(user = target, reason = f"Reaching the maximum allowed number of warnings *({warnLimit})*.")
                await ctx.reply(f"{target.display_name} has been kicked due to reaching the maximum allowed number of warnings *({warnLimit})*.")
            except Exception:
                logger.exception(f".warn failed to kick:")
                await ctx.reply("Failed to kick.")
        
    @warn.error
    async def warn_error(self, ctx: commands.Context[commands.Bot], error: commands.CommandError):
        #if user entered an invalid user
        if isinstance(error, commands.BadArgument):
            await ctx.reply("Member not found. Please mention a valid member.")
        else:
            logger.exception(f"❌ something went wrong with warn command:")
            await ctx.reply("something went wrong with **warn**.")

    #warn slash command
    @app_commands.command(
            name = "warn",
            description = Help["brief"],
            extras = Help["extras"]
    )
    @app_commands.guild_only()
    @app_commands.describe(user = "The target member to warn.", reason = "The reason to warn the target.")
    async def slashWarn(self, interaction: discord.Interaction, user: discord.Member, reason: str | None = None):
        #if user runs the command in dm
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("You can only run moderation commands in a server.", ephemeral = True)
        
        #if the user has no permission to warn
        if not interaction.user.guild_permissions.kick_members:
            return await interaction.response.send_message("You have no permission to *warn* Members.", ephemeral = True)
        
        #if the bot has no permission to warn
        if not interaction.guild.me.guild_permissions.kick_members:
            return await interaction.response.send_message("I have no permisson to *warn* Members.", ephemeral = True)
        
        #if user wants to warn himself
        if user.id == interaction.user.id:
            return await interaction.response.send_message("You can't warn yourself!", ephemeral = True)
        
        #if user wants to warn the server owner
        if user.id == interaction.guild.owner_id:
            return await interaction.response.send_message("You can't warn the server *Owner*.", ephemeral = True)
        
        #if user wants to run moderation command on the bot
        if user.id == interaction.client.application_id:
            return await interaction.response.send_message("You can't run my moderation commands on myself darling.", ephemeral = True)
        
        #if user wants to warn bots
        if user.bot:
            return await interaction.response.send_message("-agh seriously?. You can't warn bots.", ephemeral = True)
        
        #if user has lower or equal role position than target
        if user.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("You can't warn a Member with *higher or equal* role position as you.", ephemeral = True)
        
        #if the bot has lower or equal role position than target
        if user.top_role >= interaction.guild.me.top_role:
            return await interaction.response.send_message("I can't warn a Member with *higher or equal* role position as me.", ephemeral = True)
        
        #warns the target
        conn = await connection() #makes a connection to the database

        #creates the warn ID based on the last warn id
        async with conn.execute("""
        SELECT COALESCE(MAX(user_warn_id), 0) + 1
        FROM warns
        WHERE server_id = ? AND user_id = ?;
        """, (interaction.guild.id, user.id)) as cursor:
            result = await cursor.fetchone()
        warnID: int = result[0] if result else 1
            
        #inserts a new warn for given target
        await conn.execute("""
        INSERT INTO warns (server_id, user_warn_id, mod_id, user_id, reason, timestamp)
        VALUES (?, ?, ?, ?, ?, ?);
        """, (interaction.guild.id, warnID, interaction.user.id, user.id, reason, discord.utils.utcnow()))
        await conn.commit() #commits and saves the changes

        #counts the number of warns the target has
        async with conn.execute("""
        SELECT COUNT(*) FROM warns
        WHERE server_id = ? AND user_id = ?;
        """, (interaction.guild.id, user.id)) as cursor:
            result = await cursor.fetchone()
        warnCount: int = result[0] if result else 0

        await conn.close()

        await interaction.response.send_message(f"{user.mention} has been warned." + (f"\nreason: {reason}" if reason else ""))

        #if the target has over alowed number of warns, kicks it
        if warnCount >= warnLimit:
            try:
                await interaction.guild.kick(user = user, reason = f"Reaching the maximum allowed number of warnings *({warnLimit})*.")
                await interaction.response.send_message(f"{user.display_name} has been kicked due to reaching the maximum allowed number of warnings *({warnLimit})*.")
            except Exception:
                logger.exception(f".warn failed to kick:")
                await interaction.response.send_message("Failed to kick.")

    @slashWarn.error
    async def slashWarn_error(self, interaction: discord.Interaction, error: Exception):
        logger.exception(f"❌ something went wrong with /warn command:")
        try:
            await interaction.response.send_message("something went wrong with **warn**.", ephemeral = True)
        except discord.InteractionResponded:
            await interaction.followup.send("something went wrong with **warn**.", ephemeral = True)

    #گزارش
    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return
        
        content = msg.content.strip().split()
        if content[0] != "گزارش":
            return
        
        reason = " ".join(content[1:]) if len(content) >= 2 else None
        
        if not msg.guild or not isinstance(msg.author, discord.Member):
            return await msg.reply("افراد رو فقط داخل یک سرور میتونید گزارش کنید.")
        
        if not msg.author.guild_permissions.kick_members:
            return await msg.reply("شما اجازه *گزارش کردن* کسی را ندارید.")
        
        if not msg.guild.me.guild_permissions.kick_members:
            return await msg.reply("من اجازه *گزارش کردن* کسی را ندارم.")
        
        if not msg.reference or not msg.reference.message_id:
            return
        
        try:
            refMsg = await msg.channel.fetch_message(msg.reference.message_id)
            target = msg.guild.get_member(refMsg.author.id)
        except discord.NotFound:
            return
        
        if not target:
            return await msg.reply(f"\u202b{refMsg.author.display_name} عضو این سرور نیست.\u202c")
        
        if target.id == msg.author.id:
            return await msg.reply("نمی توانید خود را گزارش کنید.")
        
        if target.id == msg.guild.owner_id:
            return await msg.reply("نمی توانید *صاحب* سرور را گزارش کنید.")
        
        if target.id == msg.guild.me.id:
            return await msg.reply("نمی توانید من را گزارش کنید.")
        
        if target.bot:
            return await msg.reply("نمی توانید بات های بدبخت بیچاره را گزارش کنید.")
        
        if target.top_role >= msg.author.top_role and msg.author.id != msg.guild.owner_id:
            return await msg.reply("نمی توانید عضوی با رول *بالاتر یا برابر* از خودتان را گزارش کنید.")
        
        if target.top_role >= msg.guild.me.top_role:
            return await msg.reply("نمی توانم عضوی با رول *بالاتر یا برابر* از خودم را گزارش کنم.")
        
        conn = await connection()

        async with conn.execute("""
        SELECT COALESCE(MAX(user_warn_id), 0) + 1
        FROM warns
        WHERE server_id = ? AND user_id = ?;
        """, (msg.guild.id, target.id)) as cursor:
            result = await cursor.fetchone()
        warnID: int = result[0] if result else 1
            
        await conn.execute("""
        INSERT INTO warns (server_id, user_warn_id, mod_id, user_id, reason, timestamp)
        VALUES (?, ?, ?, ?, ?, ?);
        """, (msg.guild.id, warnID, msg.author.id, target.id, reason, discord.utils.utcnow()))
        await conn.commit()

        async with conn.execute("""
        SELECT COUNT(*) FROM warns
        WHERE server_id = ? AND user_id = ?;
        """, (msg.guild.id, target.id)) as cursor:
            result = await cursor.fetchone()
        warnCount: int = result[0] if result else 0

        await conn.close()

        await msg.reply(f"\u202b{target.mention} گزارش داده شد.\u202c" + (f"\n\u202bدلیل: {reason}\u202c" if reason else ""))

        if warnCount >= warnLimit:
            try:
                #await ctx.guild.kick(user = target, reason = f"Reached the maximum allowed number of warnings *({warnLimit})*.")
                await msg.reply(f"\u202b{target.display_name} به دلیل دریافت بیش از حد مجاز گزارش ها اخراج شد *({warnLimit})*.\u202c")
            except Exception:
                logger.exception(f"gozaresh failed to kick:")
                await msg.reply("اخراج کردن ناموفق بود.")

        await self.bot.process_commands(msg)

        
async def setup(bot: commands.Bot):
    await bot.add_cog(Warn(bot))