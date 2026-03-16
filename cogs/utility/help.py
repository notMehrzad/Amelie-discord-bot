import discord
import json
from discord.ext import commands
from discord import app_commands
from enum import Enum
from typing import Any, TypedDict
from logHandler import loggerSetup

logger = loggerSetup(__name__)


class HelpData:
    class Category(Enum):
        Anonymous = "anonymous"
        Dev = "dev"
        Economy = "economy"
        Games = "games"
        Moderation = "moderation"
        Utility = "utility"
        etc = "etc."

        def __str__(self):
            return self.name

    def __init__(
        self,
        *,
        category: Category | None,
        dmOnly: bool,
        serverOnly: bool,
        subcommands: list[str] | None,
        permissions: list[str] | None,
        help: str | None,
        brief: str,
        usage: str | None,
        aliases: list[str] | None,
        hidden: bool = False,
    ):
        self.category = category
        self.dmOnly = dmOnly
        self.serverOnly = serverOnly
        self.subcommands = subcommands
        self.permissions = permissions
        self.help = help
        self.brief = brief
        self.usage = usage
        self.aliases = aliases or []
        self.hidden = hidden

    @property
    def extras(self) -> dict[Any, Any]:
        return {
            "category": self.category,
            "dm-only": self.dmOnly,
            "server-only": self.serverOnly,
            "subcommands": self.subcommands,
            "permissions": self.permissions,
        }

    class kwargsType(TypedDict):
        help: str | None
        brief: str
        usage: str | None
        aliases: list[str]
        extras: dict[Any, Any]

    @property
    def to_kwargs(self) -> kwargsType:
        return {
            "help": self.help,
            "brief": self.brief,
            "usage": self.usage,
            "aliases": self.aliases,
            "extras": self.extras,
        }


with open("config.json") as file:
    config = json.load(file)


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    Help = HelpData(
        category=HelpData.Category.Utility,
        dmOnly=False,
        serverOnly=False,
        subcommands=None,
        permissions=None,
        help=(
            "The base help command of Amélie to show information about command(s)."
            "\n\nIf a command name is given, shows the detailed information about that command such as available subcommands, needed permission, aliases and etc."
            "\n\nIf no command name is given shows the help menu, which shows a brief overview about all commands."
        ),
        brief="The base help command.",
        usage="<command_name*[optional]*>",
        aliases=["h"],
    )

    @commands.command(name="help", **Help.to_kwargs)
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
                    f"*{command}* doesn't exist. Enter a valid command."
                )

            # if command is ephemeral, checks if the user is an admin or not
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
                cmdEmbed.add_field(name="Usage", value=f".{cmd.name} {cmd.usage}")

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

            await ctx.reply(embed=cmdEmbed)

        # shows the help menu
        else:
            if ctx.guild:
                showDev = False
            else:
                showDev = False if str(ctx.author.id) not in config["ADMINS"] else True

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
                if cmd.hidden and not showDev:
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
                        value=cmd.brief or "*No description.*",
                        inline=False,
                    )  # create fields based on fetched commands

                categoryEmbeds.append(embed)  # appends the created embed

            # if there is only one category, no buttons needed
            if len(categoryEmbeds) == 1:
                await ctx.reply(embed=categoryEmbeds[0])  # send the help menu

            else:
                view = HelpView(
                    ctx, categoryEmbeds=categoryEmbeds
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
        if command and command.lower() not in ("all", "list", "menu"):
            cmd = self.bot.get_command(
                command.lower()
            )  # fetches the command, None if not found

            # if user doesn't enter a valid command name
            if not cmd:
                return await interaction.response.send_message(
                    f"*{command}* doesn't exist. Enter a valid command.", ephemeral=True
                )

            # if command is ephemeral, checks if the user is an admin or not
            if cmd.hidden:
                if str(interaction.user.id) in config["ADMINS"]:
                    if interaction.guild and not ephemeral:
                        return await interaction.response.send_message(
                            f"You can't get help of a `Developer` command publicly in a server. (Try again in my DM or use `ephemeral` option.)",
                            ephemeral=True,
                        )
                else:
                    return await interaction.response.send_message(
                        f"Help menu for this command is not avaiable.", ephemeral=True
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
                cmdEmbed.add_field(name="Usage", value=f".{cmd.name} {cmd.usage}")

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

            await interaction.response.send_message(embed=cmdEmbed, ephemeral=ephemeral)

        # shows the help menu
        else:
            if interaction.guild:
                if ephemeral:
                    showDev = True
                else:
                    showDev = False
            else:
                showDev = (
                    False if str(interaction.user.id) not in config["ADMINS"] else True
                )

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
                if cmd.hidden and not showDev:
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
                        value=cmd.brief or "*No description.*",
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
                    interaction, categoryEmbeds=categoryEmbeds
                )  # initializes the help view
                await view.start()

    @slashHelp.error
    async def slashHelp_error(self, interaction: discord.Interaction, error: Exception):
        logger.exception(f"❌ something went wrong with /help command:")
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "something went wrong with **help**.", ephemeral=True
            )
        else:
            await interaction.followup.send(
                "something went wrong with **help**.", ephemeral=True
            )


class HelpView(discord.ui.View):
    def __init__(
        self,
        ctx: commands.Context[commands.Bot] | discord.Interaction,
        *,
        categoryEmbeds: list[discord.Embed],
        ephemeral: bool = False,
    ):
        super().__init__(timeout=60)
        if isinstance(ctx, discord.Interaction):
            self.slash = True
            self.interaction = ctx
        else:
            self.slash = False
            self.ctx = ctx
        self.user = self.interaction.user if self.slash else self.ctx.author
        self.categoryEmbeds = categoryEmbeds
        self.EmbedIndex = 0
        self.ephemeral = ephemeral

    async def start(self):
        # sends the help menu from the first category
        if self.slash:
            await self.interaction.response.send_message(
                embed=self.categoryEmbeds[0], view=self, ephemeral=self.ephemeral
            )
        else:
            self.msg = await self.ctx.reply(embed=self.categoryEmbeds[0], view=self)

    # close button
    @discord.ui.button(label="Close", style=discord.ButtonStyle.red, row=0)
    async def close(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button[discord.ui.View],
    ):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(
                "You can't control this help menu. try `/help` yourself.",
                ephemeral=True,
            )

        # deletes the menu
        if self.slash:
            await self.interaction.delete_original_response()
        else:
            await self.msg.delete()

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

        self.EmbedIndex = (self.EmbedIndex - 1) % len(
            self.categoryEmbeds
        )  # previous embed

        await interaction.response.edit_message(
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

        self.EmbedIndex = (self.EmbedIndex + 1) % len(self.categoryEmbeds)  # next embed

        await interaction.response.edit_message(
            embed=self.categoryEmbeds[self.EmbedIndex]
        )

    async def on_timeout(self):
        # disables buttons on timeout
        for btn in self.children:
            if isinstance(btn, discord.ui.Button):
                btn.disabled = True

        try:
            # edits the message to remove buttons on timeout
            if self.slash:
                await self.interaction.edit_original_response(view=None)
            else:
                await self.msg.edit(view=None)
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
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "something went wrong with **help**.", ephemeral=True
            )
        else:
            await interaction.followup.send(
                "something went wrong with **help**.", ephemeral=True
            )

        self.stop()  # stops further interaction on error


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
