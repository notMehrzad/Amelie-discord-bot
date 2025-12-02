import discord
from discord.ext import commands
from discord import app_commands
from database import connection, economyData
from datetime import timedelta, datetime
import aiosqlite
from cogs.utility.help import HelpData
from logHandler import loggerSetup

logger = loggerSetup(__name__)

def tdFormatter(td: timedelta):
    totalSeconds = int(td.total_seconds())
    h = totalSeconds // 3600
    m = (totalSeconds % 3600) // 60
    s = totalSeconds % 60
    parts: list[str] = []
    if h > 0: parts.append(f"{h}h")
    if m > 0: parts.append(f"{m}m")
    if s > 0: parts.append(f"{s}s")
    return " ".join(parts)

dailyAmount = 100 #the amount of daily to be rewarded to the users

class Daily(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    Help: HelpData = {
        "help": "",
        "brief": "Claims the Daily Reward for the user..",
        "usage": "",
        "aliases": ["d"],
        "extras": {"Category": "Economy"}
    }

    @commands.command(
            name = "daily",
            help = Help["help"],
            brief = Help["brief"],
            usage = Help["usage"],
            aliases = Help["aliases"],
            extras = Help["extras"]
    )
    async def daily(self, ctx: commands.Context[commands.Bot]):
        now = discord.utils.utcnow()

        conn = await connection() #makes a connection to the database
        conn.row_factory = aiosqlite.Row

        #checks the balance and the last daily date of the user
        async with conn.execute("""
        SELECT balance, last_daily_date FROM userbalance
        WHERE user_id = ?;
        """, (ctx.author.id,)) as cursor:
            row = await cursor.fetchone()
        #if user has no economy account, creates one
        if not row:
            await conn.execute("""
            INSERT INTO userbalance (user_id, balance, last_daily_date, created_date)
            VALUES (?, ?, ?, ?);
            """, (ctx.author.id, dailyAmount, now, now))
            await conn.commit()
            await conn.close()

            newBalance = dailyAmount
        
        #if user has an economy account
        else:
            dailyDate: datetime = datetime.fromisoformat(row["last_daily_date"]) if isinstance(row["last_daily_date"], str) else row["last_daily_date"]

            #if user trys to claim 2 dailies within a day
            if dailyDate and dailyDate + timedelta(days = 1) >= now:
                await conn.close()
                await ctx.reply(f"You must wait `{tdFormatter(dailyDate + timedelta(days = 1) - now)}` to claim your next Daily Rreward.")
                return
            
            newBalance: int = row["balance"] + dailyAmount
            
            #updates the user balance
            await conn.execute("""
            UPDATE userbalance
            SET balance = ?, last_daily_date = ?
            WHERE user_id = ?;
            """, (newBalance, now, ctx.author.id))
            await conn.commit()
            await conn.close()

        #sends the result
        resultEmbed = discord.Embed(
            title = "Daily Reward !",
            description = f"You have claimed your Daily Reward for today.\nCurrent balance: *{newBalance} {economyData["icon"]}* {economyData["name"]}s",
            color = discord.Color.blurple(),
            timestamp = now
        )
        await ctx.reply(embed = resultEmbed)

    @daily.error
    async def daily_error(self, ctx: commands.Context[commands.Bot], error: Exception):
        logger.exception(f"❌ something went wrong with daily command:")
        await ctx.reply("something went wrong with **daily**.")

    #daily slash command
    @app_commands.command(
        name = "daily",
        description = Help["brief"],
        extras = Help["extras"]
    )
    async def slashDaily(self, interaction: discord.Interaction):
        now = discord.utils.utcnow()

        conn = await connection() #makes a connection to the database
        conn.row_factory = aiosqlite.Row

        #checks the balance and the last daily date of the user
        async with conn.execute("""
        SELECT balance, last_daily_date FROM userbalance
        WHERE user_id = ?;
        """, (interaction.user.id,)) as cursor:
            row = await cursor.fetchone()
        #if user has no economy account, creates one
        if not row:
            await conn.execute("""
            INSERT INTO userbalance (user_id, balance, last_daily_date, created_date)
            VALUES (?, ?, ?, ?);
            """, (interaction.user.id, dailyAmount, now, now))
            await conn.commit()
            await conn.close()

            newBalance = dailyAmount
        
        #if user has an economy account
        else:
            dailyDate: datetime = datetime.fromisoformat(row["last_daily_date"]) if isinstance(row["last_daily_date"], str) else row["last_daily_date"]

            #if user trys to claim 2 dailies within a day
            if dailyDate and dailyDate + timedelta(days = 1) >= now:
                await conn.close()
                await interaction.response.send_message(f"You must wait `{tdFormatter(dailyDate + timedelta(days = 1) - now)}` to claim your next Daily Rreward.", ephemeral = True)
                return
            
            newBalance: int = row["balance"] + dailyAmount
            
            #updates the user balance
            await conn.execute("""
            UPDATE userbalance
            SET balance = ?, last_daily_date = ?
            WHERE user_id = ?;
            """, (newBalance, now, interaction.user.id))
            await conn.commit()
            await conn.close()

        #sends the result
        resultEmbed = discord.Embed(
            title = "Daily Reward !",
            description = f"You have claimed your Daily Reward for today.\nCurrent balance: *{newBalance} {economyData["icon"]}* {economyData["name"]}s",
            color = discord.Color.blurple(),
            timestamp = now
        )
        await interaction.response.send_message(embed = resultEmbed)
        
    @slashDaily.error
    async def slashDaily_error(self, interaction: discord.Interaction, error: Exception):
        logger.exception(f"❌ something went wrong with /daily command:")
        try:
            await interaction.response.send_message("something went wrong with **daily**.", ephemeral = True)
        except discord.InteractionResponded:
            await interaction.followup.send("something went wrong with **daily**.", ephemeral = True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Daily(bot))