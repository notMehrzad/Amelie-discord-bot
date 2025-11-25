import discord
from discord.ext import commands
from discord import app_commands
from cogs.utility.help import HelpData
from logHandler import loggerSetup

logger = loggerSetup(__name__)

class Say(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    Help: HelpData = {
        "help": "",
        "brief": "Says something in the channel.",
        "usage": "<message>",
        "aliases": ["echo"],
        "extras": {"Category": "Utility"}
    }

    @commands.command(
            name = "say",
            help = Help["help"],
            brief = Help["brief"],
            usage = Help["usage"],
            aliases = Help["aliases"],
            extras = Help["extras"]
    )
    async def say(self, ctx: commands.Context[commands.Bot], channel: discord.abc.GuildChannel | discord.Thread | discord.abc.PrivateChannel | str | None, *, message: str | None):
        #if user doesn't enter a channel
        if not channel:
            return await ctx.reply("You must enter the channel you want to say something in. (or *here* to choose the current channel)")
        
        #if user entes an invalid channel
        if isinstance(channel, str):
            if channel.lower() == "here":
                targetChannel = ctx.channel
            else:
                return await ctx.reply("Enter a valid channel.")
        else:
            targetChannel = channel
        
        if not isinstance(targetChannel, discord.abc.Messageable):
            return await ctx.reply("The given channel is not messageable.")
        
        #if target channel is a server channel, checks permissions
        if isinstance(ctx.author, discord.Member) and isinstance(ctx.me, discord.Member):
            #if user has no permission to send message in the target channel
            if not targetChannel.permissions_for(ctx.author).send_messages:
                return await ctx.reply("You have no permission to *say and send* messages in this channel.")
            
            #if the bot has no permission to send message in the target channel
            if not targetChannel.permissions_for(ctx.me).send_messages:
                return await ctx.reply("I have no permission to *say and send* messages in this channel.")
        
        #if user doesn't enter message
        if not message:
            return await ctx.reply("You must write your text to be said.")
        
        await targetChannel.send(message) #sends the message in the channel

    @say.error
    async def say_error(self, ctx: commands.Context[commands.Bot], error: Exception):
        logger.exception(f"❌ something went wrong with say command:")
        await ctx.reply("something went wrong with **say**.")

    #say slash command
    @app_commands.command(
        name = "say",
        description = Help["brief"],
        extras = Help["extras"]
    )
    @app_commands.describe(message = "The message to be said.", channel = "The channel you want to say something in.", visible_slash_command = "Whether it should be visible if it was a slash command or not.")
    async def slashSay(self, interaction: discord.Interaction, message: str, channel: discord.abc.GuildChannel | discord.Thread | None = None, visible_slash_command: bool = True):
        targetChannel = interaction.channel if not channel else channel

        if not isinstance(targetChannel, discord.abc.Messageable):
            return await interaction.response.send_message("The given channel is not messageable.", ephemeral = True)
        
        #if target channel is a server channel, checks permissions
        if isinstance(interaction.user, discord.Member) and interaction.guild:
            #if user has no permission to send message in the target channel
            if not targetChannel.permissions_for(interaction.user).send_messages:
                return await interaction.response.send_message("You have no permission to *say and send* messages in this channel.", ephemeral = True)
            
            #if the bot has no permission to send message in the target channel
            if not targetChannel.permissions_for(interaction.guild.me).send_messages:
                return await interaction.response.send_message("I have no permission to *say and send* messages in this channel.", ephemeral = True)
        
        #sends the message in the current channel
        if targetChannel == interaction.channel:
            if visible_slash_command:
                await interaction.response.send_message(message)
            else:
                await interaction.response.defer(ephemeral = True)
                await targetChannel.send(message)
                await interaction.followup.send("Sent.")

        #sends the message in the target channel
        else:
            await interaction.response.defer(ephemeral = True)
            await targetChannel.send(message)
            await interaction.followup.send("Sent.")

    @slashSay.error
    async def slashSay_error(self, interaction: discord.Interaction, error: Exception):
        logger.exception(f"❌ something went wrong with /say command:")
        try:
            await interaction.response.send_message("something went wrong with **say**.", ephemeral = True)
        except discord.InteractionResponded:
            await interaction.followup.send("something went wrong with **say**.", ephemeral = True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Say(bot))