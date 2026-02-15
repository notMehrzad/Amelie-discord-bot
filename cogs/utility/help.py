import discord
from discord.ext import commands
from discord import app_commands
import json
from typing import Any
from logHandler import loggerSetup

logger = loggerSetup(__name__)


class HelpData:
    def __init__(
        self,
        category: str | None = None,
        dmOnly: bool = False,
        serverOnly: bool = False,
        subcommands: list[str] = [],
        permissions: list[str] = [],
        help: str | None = None,
        brief: str = "",
        usage: str | None = None,
        aliases: list[str] = [],
    ):
        self.category = category
        self.dmOnly = dmOnly
        self.serverOnly = serverOnly
        self.subcommands = subcommands
        self.permissions = permissions
        self.help = help
        self.brief = brief
        self.usage = usage
        self.aliases = aliases

    @property
    def extras(self) -> dict[Any, Any]:
        return {
            "category": self.category,
            "dm-only": self.dmOnly,
            "server-only": self.serverOnly,
            "subcommands": self.subcommands,
            "permissions": self.permissions,
        }


with open("config.json") as file:
    config = json.load(file)


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    Help = HelpData(
        category="Utility",
        help=(
            "Shows the help menu which gives a brief information about Commands."
            "\nEnter a Command name for its full detail such as its application, usage, necessery permissions (if any) and etc. or don't, to get the help menu."
        ),
        brief="Shows the help menu.",
        usage="<command_name*[optional]*>",
        aliases=["h"],
    )

    @commands.command(
        name="help",
        help=Help.help,
        brief=Help.brief,
        usage=Help.usage,
        aliases=Help.aliases,
        extras=Help.extras,
    )
    async def help(
        self, ctx: commands.Context[commands.Bot], command: str | None = None
    ):
        # help for specific command
        if command and command.lower() not in ("all", "list", "menu"):
            cmd = self.bot.get_command(
                command.lower()
            )  # fetches the command, None if not found

            # if user doesn't enter a valid command name
            if not cmd:
                return await ctx.reply(
                    f"*{command}* doesn't exist. enter a valid command."
                )

            # if command is hidden, checks if the user is an admin or not
            if cmd.hidden and str(ctx.author.id) not in config["ADMINS"]:
                return await ctx.reply(f"Help menu for this command is not avaiable.")

            cmdEmbed = discord.Embed(
                title="." + cmd.name,
                description=cmd.help
                or cmd.brief
                or "*No description provided for this command.*",
                color=discord.Color.blurple(),
            ).set_author(name="Help")
            # if command has aliases
            if cmd.aliases:
                cmdEmbed.add_field(name="Aliases", value=" | ".join(cmd.aliases))

            # if command has usage
            if cmd.usage:
                cmdEmbed.add_field(name="Usage", value=f"/{cmd.name} {cmd.usage}")

            # if command has subcommands
            if cmd.extras["subcommands"]:
                cmdEmbed.add_field(
                    name="Subcommands", value=" | ".join(cmd.extras["subcommands"])
                )

            # if command is dm only
            if cmd.extras["dm-only"]:
                cmdEmbed.add_field(name="DM-only", value="Yes")

            # if command is server only
            if cmd.extras["server-only"]:
                cmdEmbed.add_field(name="Server-only", value="Yes")

            # if command needs certain permissions
            if cmd.extras["permissions"]:
                cmdEmbed.add_field(
                    name="Permissions", value=" | ".join(cmd.extras["permissions"])
                )

            # if command has extra information
            for key, value in cmd.extras.items():
                if key == "category":
                    continue
                cmdEmbed.add_field(
                    name=key, value=value
                )  # add extra information to fields

            await ctx.reply(embed=cmdEmbed)

        # shows the help menu
        else:
            categorized: dict[str, list[commands.Command[Any, Any, Any]]] = (
                {}
            )  # a dictionary to list categories and commands
            # example:
            # {
            #   "Moderation": ["ban", "kick"],
            #   "Utils": ["ping", "help"]
            # }

            # fetches all registered commadns
            for cmd in self.bot.commands:
                if cmd.hidden:
                    continue

                category = cmd.extras.get(
                    "category", "etc."
                )  # fetches each commands category
                categorized.setdefault(category, []).append(
                    cmd
                )  # adds the command and its category to categorized

            # sorts command list for every category in categorized dictionary
            for category in categorized:
                categorized[category].sort(key=lambda cmd: cmd.name)

            categorized = dict(
                sorted(categorized.items(), key=lambda item: item[0].lower())
            )  # rebuilds the dictionary but sorted keys this time

            categoryEmbeds: list[discord.Embed] = (
                []
            )  # a list to store embeds for each category

            # fetches categorized data
            for category, cmdList in categorized.items():
                embed = discord.Embed(
                    title=f"{category}", color=discord.Color.blurple()
                ).set_author(name="Help Menu")
                for cmd in cmdList:
                    embed.add_field(
                        name="." + cmd.name,
                        value=cmd.brief or "*No description*",
                        inline=False,
                    )  # create fields based on fetched commands

                categoryEmbeds.append(embed)  # appends the created embed

            # if there is only one category, no buttons needed
            if len(categoryEmbeds) == 1:
                await ctx.reply(embed=categoryEmbeds[0])  # send the help menu

            else:
                view = HelpView(
                    ctx, ctx.author, categoryEmbeds
                )  # initializes the help view
                await view.start()

    @help.error
    async def help_error(self, ctx: commands.Context[commands.Bot], error: Exception):
        logger.exception(f"❌ something went wrong with help command:")
        await ctx.reply("something went wrong with **help**.")

    # help slash command
    @app_commands.command(name="help", description=Help.brief, extras=Help.extras)
    @app_commands.describe(
        command="The command to get the help of.",
        ephemeral="Whether the help menu should be ephemeral or not.",
    )
    async def slashHelp(
        self,
        interaction: discord.Interaction,
        command: str | None = None,
        ephemeral: bool = False,
    ):
        # help for specific command
        if command:
            cmd = self.bot.get_command(
                command.lower()
            )  # fetches the command, None if not found

            # if the cmd is not found
            if not cmd:
                return await interaction.response.send_message(
                    f"*{command}* doesn't exist. enter a valid command.", ephemeral=True
                )

            # if command is hidden, checks if the user is an admin or not
            if cmd.hidden and str(interaction.user.id) not in config["ADMINS"]:
                return await interaction.response.send_message(
                    f"Help menu for this command is not avaiable."
                )

            cmdEmbed = discord.Embed(
                title="/" + cmd.name,
                description=cmd.help
                or cmd.brief
                or "*No description provided for this command.*",
                color=discord.Color.blurple(),
            ).set_author(name="Help")
            # if command has aliases
            if cmd.aliases:
                cmdEmbed.add_field(name="Aliases", value=" | ".join(cmd.aliases))

            # if command has usage
            if cmd.usage:
                cmdEmbed.add_field(name="Usage", value=f"/{cmd.name} {cmd.usage}")

            # if command has subcommands
            if cmd.extras["subcommands"]:
                cmdEmbed.add_field(
                    name="Subcommands", value=" | ".join(cmd.extras["subcommands"])
                )

            # if command is dm only
            if cmd.extras["dm-only"]:
                cmdEmbed.add_field(name="DM-only", value="Yes")

            # if command is server only
            if cmd.extras["server-only"]:
                cmdEmbed.add_field(name="Server-only", value="Yes")

            # if command needs certain permissions
            if cmd.extras["permissions"]:
                cmdEmbed.add_field(
                    name="Permissions", value=" | ".join(cmd.extras["permissions"])
                )

            # if command has extra information
            for key, value in cmd.extras.items():
                if key == "category":
                    continue
                cmdEmbed.add_field(
                    name=key, value=value
                )  # add extra information to fields

            await interaction.response.send_message(embed=cmdEmbed, ephemeral=ephemeral)

        # shows the help menu
        else:
            categorized: dict[str, list[commands.Command[Any, Any, Any]]] = (
                {}
            )  # a dictionary to list categories and commands
            # example:
            # {
            #   "Moderation": ["ban", "kick"],
            #   "Utils": ["ping", "help"]
            # }

            # fetches all registered commadns
            for cmd in self.bot.commands:
                if cmd.hidden:
                    continue

                category = cmd.extras.get(
                    "category", "etc."
                )  # fetches each commands category
                categorized.setdefault(category, []).append(
                    cmd
                )  # adds the command and its category to categorized

            # sorts command list for every category in categorized dictionary
            for category in categorized:
                categorized[category].sort(key=lambda cmd: cmd.name)

            categorized = dict(
                sorted(categorized.items(), key=lambda item: item[0].lower())
            )  # rebuilds the dictionary but sorted keys this time

            categoryEmbeds: list[discord.Embed] = (
                []
            )  # a list to store embeds for each category

            # fetches categorized data
            for category, cmdList in categorized.items():
                embed = discord.Embed(
                    title=f"{category}", color=discord.Color.blurple()
                ).set_author(name="Help Menu")
                for cmd in cmdList:
                    embed.add_field(
                        name="/" + cmd.name,
                        value=cmd.brief or "*No description*",
                        inline=False,
                    )  # create fields based on fetched commands

                categoryEmbeds.append(embed)  # appends the created embed

            # if there is only one category, no buttons needed
            if len(categoryEmbeds) == 1:
                await interaction.response.send_message(
                    embed=categoryEmbeds[0], ephemeral=ephemeral
                )  # send the help menu

            else:
                view = HelpView(
                    interaction, interaction.user, categoryEmbeds, ephemeral
                )  # initializes the help view
                await view.start()

    @slashHelp.error
    async def slashHelp_error(self, interaction: discord.Interaction, error: Exception):
        logger.exception(f"❌ something went wrong with /help command:")
        try:
            await interaction.response.send_message(
                "something went wrong with **help**.", ephemeral=True
            )
        except discord.InteractionResponded:
            await interaction.followup.send(
                "something went wrong with **help**.", ephemeral=True
            )


class HelpView(discord.ui.View):
    def __init__(
        self,
        ctx: commands.Context[commands.Bot] | discord.Interaction,
        user: discord.abc.User,
        categoryEmbeds: list[discord.Embed],
        hidden: bool = False,
    ):
        super().__init__(timeout=90)
        if isinstance(ctx, discord.Interaction):
            self.slash = True
            self.interaction = ctx
        else:
            self.slash = False
            self.ctx = ctx
        self.user = user
        self.categoryEmbeds = categoryEmbeds
        self.EmbedIndex = 0
        self.hidden = hidden

    async def start(self):
        # sends the help menu from the first category
        if not self.slash:
            self.msg = await self.ctx.reply(embed=self.categoryEmbeds[0], view=self)
        else:
            await self.interaction.response.send_message(
                embed=self.categoryEmbeds[0], view=self, ephemeral=self.hidden
            )

    # close button
    @discord.ui.button(label="Close", style=discord.ButtonStyle.red, row=0)
    async def close(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button[discord.ui.View],
    ):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(
                "You can't control this help menu. try help command yourself.",
                ephemeral=True,
            )

        # deletes the menu
        if not self.slash:
            await self.msg.delete()
        else:
            await self.interaction.delete_original_response()
        self.stop()

    # previous button
    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.grey, row=0)
    async def previous(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button[discord.ui.View],
    ):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(
                "You can't control this help menu. try help command yourself.",
                ephemeral=True,
            )

        await interaction.response.defer(ephemeral=self.hidden)

        self.EmbedIndex = (self.EmbedIndex - 1) % len(
            self.categoryEmbeds
        )  # previous embed
        if not self.slash:
            await self.msg.edit(embed=self.categoryEmbeds[self.EmbedIndex])
        else:
            await self.interaction.edit_original_response(
                embed=self.categoryEmbeds[self.EmbedIndex]
            )

    # next button
    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.grey, row=0)
    async def next(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button[discord.ui.View],
    ):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(
                "You can't control this help menu. try help command yourself.",
                ephemeral=True,
            )

        await interaction.response.defer()

        self.EmbedIndex = (self.EmbedIndex + 1) % len(self.categoryEmbeds)  # next embed
        if not self.slash:
            await self.msg.edit(embed=self.categoryEmbeds[self.EmbedIndex])
        else:
            await self.interaction.edit_original_response(
                embed=self.categoryEmbeds[self.EmbedIndex]
            )

    async def on_timeout(self):
        # disables buttons on timeout
        for btn in self.children:
            if isinstance(btn, discord.ui.Button):
                btn.disabled = True

        try:
            # edits the message to remove buttons on timeout
            if not self.slash:
                await self.msg.edit(view=None)
            else:
                await self.interaction.edit_original_response(view=None)
        except discord.NotFound:
            pass

        self.stop()  # stops further interaction on timeout

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item[discord.ui.View],
    ):
        logger.exception(
            f"❌ something went wrong with help interaction - button: {getattr(item, 'emoji', 'unknown')}"
        )
        try:
            await interaction.response.send_message(
                "something went wrong with **help**.", ephemeral=True
            )
        except Exception:
            pass

        self.stop()  # stops further interaction on error


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
