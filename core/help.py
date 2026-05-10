"""This file contains the structure and logic of the command's help.

It makes it easier to make and generate helps for various commands rather than
old-fashion hand written helps.
"""

from enum import Enum
from typing import Any, TypedDict

from logHandler import loggerSetup

logger = loggerSetup(__name__)
__all__ = ["CommandCategory", "HelpData"]


class CommandCategory(Enum):
    """The class for different command categories."""

    Anonymous = "Anonymous"
    Dev = "Dev"
    Economy = "Economy"
    Games = "Games"
    Moderation = "Moderation"
    Utility = "Utility"
    Misc = "Misc"

    def __str__(self) -> str:
        return self.value


class KwargsTyped(TypedDict):
    help: str | None
    brief: str
    usage: str | None
    aliases: list[str]
    extras: dict[str, Any]


class HelpData:
    """The class representing a command help."""

    def __init__(
        self,
        *,
        category: CommandCategory,
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
        """Initiates the instance.

        Args:
            category (CommandCategory): The category of the command.
            dmOnly (bool): If the command is DM stricted.
            serverOnly (bool): If the command is guild(server) stricted.
            subcommands (list[str] | None): The subcommands of the command.
            permissions (list[str] | None): The required permissions to run the command.
            help (str | None): The long help text for the command.
            brief (str): The short help text for the command.
            usage (str | None): The usage format of the command.
            aliases (list[str] | None): Aliases of the command.
            hidden (bool, optional): If the command should be hidden. Defaults to False.
        """

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
    def extras(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "dm-only": self.dmOnly,
            "server-only": self.serverOnly,
            "subcommands": self.subcommands,
            "permissions": self.permissions,
        }

    @property
    def kwargs(self) -> KwargsTyped:
        """returns attributes as a dict(keywords) to pass.

        Returns:
            dict[str, Any]: All the attributes as keywords.
        """

        return {
            "help": self.help,
            "brief": self.brief,
            "usage": self.usage,
            "aliases": self.aliases,
            "extras": self.extras,
        }
