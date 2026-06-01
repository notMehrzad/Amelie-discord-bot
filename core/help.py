"""Contains the structure and logic of the command's help.

It makes it easier to make and generate helps for various commands rather than
old-fashion handwritten helps.
"""

from __future__ import annotations

__all__ = ["HelpData"]

from enum import Enum
from typing import Any, TypedDict, final

from core.log_handler import logger_setup

logger = logger_setup(__name__)


class _KwargsTyped(TypedDict):
    help: str | None
    brief: str
    usage: str | None
    aliases: list[str]
    extras: dict[str, Any]


@final
class HelpData:
    """The class representing a command help."""

    class CommandCategory(Enum):
        """The class for different command categories."""

        ANONYMOUSE = "Anonymous"
        DEV = "Dev"
        ECONOMY = "Economy"
        GAMES = "Games"
        MODERATION = "Moderation"
        UTILITY = "Utility"
        MISC = "Misc"

    def __init__(  # noqa: PLR0913
        self,
        *,
        category: CommandCategory,
        dm_only: bool,
        server_only: bool,
        subcommands: list[str] | None,
        permissions: list[str] | None,
        help_: str | None,
        brief: str,
        usage: str | None,
        aliases: list[str] | None,
        hidden: bool = False,
    ) -> None:
        """Initialize help data.

        Args:
            category (CommandCategory): The category of the command.
            dm_only (bool): If the command is DM-restricted.
            server_only (bool): If the command is guild-restricted.
            subcommands (list[str] | None): The subcommands of the command.
            permissions (list[str] | None): The required permissions to run the command.
            help_ (str | None): The long help text for the command.
            brief (str): The short help text for the command.
            usage (str | None): The usage format of the command.
            aliases (list[str] | None): Aliases of the command.
            hidden (bool, optional): If the command should be hidden. Defaults to False.

        """
        self.category = category
        self.dmOnly = dm_only
        self.serverOnly = server_only
        self.subcommands = subcommands
        self.permissions = permissions
        self.help = help_
        self.brief = brief
        self.usage = usage
        self.aliases = aliases or []
        self.hidden = hidden

    @property
    def _extras(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "dm-only": self.dmOnly,
            "server-only": self.serverOnly,
            "subcommands": self.subcommands,
            "permissions": self.permissions,
        }

    @property
    def kwargs(self) -> _KwargsTyped:
        """Return attributes as a dict(keywords) to pass.

        Returns:
            dict[str, Any]: All the attributes as keywords.

        """
        return {
            "help": self.help,
            "brief": self.brief,
            "usage": self.usage,
            "aliases": self.aliases,
            "extras": self._extras,
        }
