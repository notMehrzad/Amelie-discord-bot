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
    async def say(self, ctx: commands.Context[commands.Bot], *, message: str | None):
        if not message:
            return await ctx.reply("You must write your text to be said.")
        
        await ctx.send(message)

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
    @app_commands.describe(message = "The message to be said.", visible_slash_command = "Whether it should be visible if it was a slash command or not.")
    async def slashSay(self, interaction: discord.Interaction, message: str, visible_slash_command: bool = True):
        if visible_slash_command:
            await interaction.response.send_message(message)
        else:
            if isinstance(interaction.channel, discord.TextChannel):
                await interaction.response.defer(ephemeral = True)
                await interaction.channel.send(message)
                await interaction.edit_original_response(content = "Sent.")

    @slashSay.error
    async def slashSay_error(self, interaction: discord.Interaction, error: Exception):
        logger.exception(f"❌ something went wrong with /say command:")
        try:
            await interaction.response.send_message("something went wrong with **say**.", ephemeral = True)
        except discord.InteractionResponded:
            await interaction.followup.send("something went wrong with **say**.", ephemeral = True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Say(bot))