import discord
from discord.ext import commands
from discord import app_commands
from logHandler import loggerSetup

logger = loggerSetup(__name__)

class Say(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
            name = "say",
            extras = {"Category": "Utility"},
            aliases = ["echo"],
            usage = "<message>",
            brief = "Says something in the channel.",
            help = (
                "Says a custom message inside the channel."
            )
    )
    async def say(self, ctx: commands.Context[commands.Bot], *, text: str | None):
        if not text:
            return await ctx.reply("You must write your text to be said.")
        
        await ctx.send(text)

    @say.error
    async def say_error(self, ctx: commands.Context[commands.Bot], error: Exception):
        logger.exception(f"❌ something went wrong with say command:")
        await ctx.reply("something went wrong with **say**.")

    #say slash command
    @app_commands.command(
        name = "say",
        description = "Says something in the channel.",
        extras = {"Category": "Utility"}
    )
    async def slashSay(self, interaction: discord.Interaction, text: str, visible_slash_command: bool = True):
        if visible_slash_command:
            await interaction.response.send_message(text)
        else:
            await interaction.response.defer(ephemeral = True)
            if isinstance(interaction.channel, discord.TextChannel):
                await interaction.channel.send(text)
            await interaction.edit_original_response(content = "Sent.")

    @slashSay.error
    async def slashSay_error(self, interaction: discord.Interaction, error: Exception):
        logger.exception(f"❌ something went wrong with /say command:")
        await interaction.response.send_message("something went wrong with **say**.", ephemeral = True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Say(bot))