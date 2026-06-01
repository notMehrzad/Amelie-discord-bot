"""Contains useful tools that can be used in several files.

All tools that may be used in several modules must be defined here.
"""

from __future__ import annotations

__all__ = ["timedelta_formater"]

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import timedelta


def timedelta_formater(td: timedelta) -> str:
    """Return a human-readable format of a timedelta.

    Args:
        td (timedelta): The timedelta to be formated.

    Returns:
        str: The formated timedelta.

    """
    total_seconds = int(td.total_seconds())

    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60

    parts: list[str] = []
    if h > 0:
        parts.append(f"{h}h")
    if m > 0:
        parts.append(f"{m}m")
    if s > 0:
        parts.append(f"{s}s")

    return " ".join(parts)
