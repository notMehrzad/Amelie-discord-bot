"""This file contains useful tools that can be used in several files.
All tools that may be used in several files must be defined here.
"""

from datetime import timedelta


def timedelta_formater(td: timedelta) -> str:
    """Returns a human-readable format of a timedelta.

    Args:
        td (timedelta): The timedelta to be formated.

    Returns:
        str: The formated timedelta.
    """

    totalSeconds = int(td.total_seconds())

    h = totalSeconds // 3600
    m = (totalSeconds % 3600) // 60
    s = totalSeconds % 60

    parts: list[str] = []
    if h > 0:
        parts.append(f"{h}h")
    if m > 0:
        parts.append(f"{m}m")
    if s > 0:
        parts.append(f"{s}s")

    return " ".join(parts)
