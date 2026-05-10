from contextlib import asynccontextmanager
from enum import Enum
from typing import Any, Iterable

import aiosqlite
import discord
from discord.ext import commands

from logHandler import loggerSetup

DATABASE_PATH = "bot_database.db"

logger = loggerSetup(__name__)
__all__ = ["tableInitialize", "execute", "fetchone", "fetchall"]


class Session:
    sessions: dict[tuple[int, "Types"], "Session"] = {}

    class Types(Enum):
        gambling = "gambling"
        messaging = "messaging"

    def __init__(self, userId: int, type: Types):
        self.userId = userId
        self.type = type
        Session.sessions[(self.userId, self.type)] = self

    def close(self):
        try:
            Session.sessions.pop((self.userId, self.type))
        except KeyError:
            pass

    async def collectMessage(self, bot: commands.Bot, *, dmOnly: bool):
        def check(msg: discord.Message):
            return (
                (msg.author.id == self.userId and not msg.guild)
                if dmOnly
                else msg.author.id == self.userId
            )

        self.messages: list[discord.Message] = []
        while (self.userId, self.type) in Session.sessions:
            msg = await bot.wait_for("message", check=check)
            self.messages.append(msg)


@asynccontextmanager
async def _connect():
    async with aiosqlite.connect(DATABASE_PATH) as conn:  # connects to the db file
        await conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = aiosqlite.Row
        try:
            yield conn
        except:
            await conn.rollback()
            raise


# initiates the tables
async def tableInitialize(*tables: str) -> None:
    """This function is used to initiate the new database tables.

    Raises:
        ValueError: If no table is given.
    """

    # if no table is given
    if not tables:
        raise ValueError("At least one table must be given to initiate.")

    # executes for every each table
    async with _connect() as conn:
        for table in tables:
            await conn.execute(table)
        await conn.commit()


async def execute(query: str, params: Iterable[Any] | None = None) -> aiosqlite.Cursor:
    """This function is a helper, used to execute a query in aiosqlite.

    Args:
        query (str): The query to be executed.
        params (Iterable[Any] | None, optional): The parameters to be passed. Defaults to None.

    Returns:
        Cursor: The cursor.
    """

    async with _connect() as conn:
        async with conn.execute(query, params) as cursor:
            await conn.commit()
            return cursor


async def fetchone(
    query: str, params: Iterable[Any] | None = None
) -> aiosqlite.Row | None:
    """This function is a helper, used to fetch a row from given parameters.

    Args:
        query (str): The query to be fetched.
        params (Iterable[Any] | None, optional): The parameters to be passed. Defaults to None.

    Returns:
        Row | None: The fetched Row if it's found. `None`, otherwise.
    """

    async with _connect() as conn:
        async with conn.execute(query, params) as cursor:
            return await cursor.fetchone()


async def fetchall(
    query: str, params: Iterable[Any] | None = None
) -> Iterable[aiosqlite.Row]:
    """This function is a helper, used to fetch all possible rows with given parameters.

    Args:
        query (str): The query to be fethced.
        params (Iterable[Any] | None, optional): The parameters to be passed. Defaults to None.

    Returns:
        Iterable[Row]: An `Iterable` containing the fetched rows.
    """

    async with _connect() as conn:
        async with conn.execute(query, params) as cursor:
            return await cursor.fetchall()
