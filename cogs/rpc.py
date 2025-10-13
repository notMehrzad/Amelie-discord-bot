from discord.ext import commands
import random

choices = ["rock", "paper", "scissors"]
beats = {
    "rock": "scissors",
    "paper": "rock",
    "scissors": "paper"
}

class Rpc(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name = "rpc")
    async def rpc(self, ctx: commands.Context, user_choice: str = None):
        user_choice = user_choice.lower() if user_choice else None
        if user_choice is None or user_choice not in choices:
            await ctx.reply("you must choose between *rock, paper, scissors!*.")
            return
        
        bot_choice = random.choice(choices)

        #tie
        if user_choice == bot_choice:
            await ctx.reply(f"**It was a Tie!**\nboth chose {user_choice}")

        #user wins
        elif beats[user_choice] == bot_choice:
            await ctx.reply(f"**You Won!**\nmy choice: {bot_choice} | your choice: {user_choice}")

        else:
            await ctx.reply(f"**I won!**\nmy choice: {bot_choice} | your choice: {user_choice}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Rpc(bot))