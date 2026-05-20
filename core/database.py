"""This files contains the logic and structure of the database, aiosqlite, that Amelie uses.
It simplifies the process of executing or fetching data using a handler that manages creating connection, commiting
changes and closing connection automatically with just simple functions.
Custom functions can be made and used like _run(CustomFunction).
"""

from enum import Enum
from typing import Any, Awaitable, Callable, TypeVar

import aiosqlite
import discord
from discord.ext import commands

from core.dbconstants import *
from core.logHandler import loggerSetup

DATABASE_PATH = "bot_database.db"
TABLES = (
    f"""
    CREATE TABLE IF NOT EXISTS {AccountTable.TABLE_NAME} (
        {AccountTable.COL_USER_ID} INTEGER PRIMARY KEY NOT NULL,
        {AccountTable.COL_BALANCE} INTEGER NOT NULL,
        {AccountTable.COL_CREATED_AT} INTEGER NOT NULL,
        {AccountTable.COL_LAST_DAILY_DATE} INTEGER,
        {AccountTable.COL_LAST_WORK_DATE} INTEGER
    );
    """,
    f"""
    CREATE TABLE IF NOT EXISTS {CheckTable.TABLE_NAME} (
        {CheckTable.COL_ID} TEXT PRIMARY KEY NOT NULL,
        {CheckTable.COL_SENDER_ID} INTEGER NOT NULL,
        {CheckTable.COL_AMOUNT} INTEGER NOT NULL,
        {CheckTable.COL_RECEIVER_ID} INTEGER NOT NULL,
        {CheckTable.COL_REASON} TEXT,
        {CheckTable.COL_DATE} INTEGER NOT NULL,
        {CheckTable.COL_DEPOSITED} INTEGER DEFAULT 0
    );
    """,
    f"""
    CREATE TABLE IF NOT EXISTS {TransactionTable.TABLE_NAME} (
        {TransactionTable.COL_ID} TEXT PRIMARY KEY NOT NULL,
        {TransactionTable.COL_TYPE} TEXT NOT NULL,
        {TransactionTable.COL_USER_ID} INTEGER NOT NULL,
        {TransactionTable.COL_AMOUNT} INTEGER NOT NULL,
        {TransactionTable.COL_DATE} INTEGER NOT NULL,
        {TransactionTable.COL_RECEIVER_ID} INTEGER,
        {TransactionTable.COL_REASON} TEXT
    );
    """,
)

T = TypeVar("T")
logger = loggerSetup(__name__)
__all__ = ["execute", "fetchone", "fetchall", "initialize_tables"]


class Session:
    sessions: dict[tuple[int, "Types"], "Session"] = {}

    class Types(Enum):
        GAMBLING = "GAMBLING"
        MESSAGING = "MESSAGING"

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
        def __check(msg: discord.Message):
            return (
                (msg.author.id == self.userId and not msg.guild)
                if dmOnly
                else msg.author.id == self.userId
            )

        self.messages: list[discord.Message] = []
        while (self.userId, self.type) in Session.sessions:
            msg = await bot.wait_for("message", check=__check)
            self.messages.append(msg)


async def _run(func: Callable[..., Awaitable[T]]) -> T:
    """Every database function must be called inside this function to be run and executed properly.

    Args:
        func (Callable[..., Awaitable[T]]): The function to be run.

    Returns:
        T: Varries from function it runs to another.
    """

    async with aiosqlite.connect(DATABASE_PATH) as conn:  # connects to the database
        await conn.execute("PRAGMA foreign_keys = ON")
        await conn.execute("PRAGMA journal_mode = WAL")

        return await func(conn)  # runs the command


async def execute(query: str, params: tuple[Any, ...] | None = None) -> None:
    """This function is a helper, used to execute a query in aiosqlite.

    Args:
        query (str): The query to be executed.
        params (tuple[Any, ...] | None, optional): The parameters to be passed. Defaults to None.
    """

    async def _execute(conn: aiosqlite.Connection) -> None:
        try:
            await conn.execute(query, params)
            await conn.commit()
        except:
            await conn.rollback()
            raise

    return await _run(_execute)


async def fetchone(
    query: str, params: tuple[Any, ...] | None = None
) -> dict[str, Any] | None:
    """This function is a helper, used to fetch a row from given parameters.

    Args:
        query (str): The query to be fetched.
        params (tuple[Any, ...] | None, optional): The parameters to be passed. Defaults to None.

    Returns:
        dict[str, Any] | None: The fetched Row if it's found. `None`, otherwise.
    """

    async def _fetchone(conn: aiosqlite.Connection) -> dict[str, Any] | None:
        try:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(query, params) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
        except:
            await conn.rollback()
            raise

    return await _run(_fetchone)


async def fetchall(
    query: str, params: tuple[Any, ...] | None = None
) -> list[dict[str, Any]] | None:
    """This function is a helper, used to fetch all possible rows with given parameters.

    Args:
        query (str): The query to be fethced.
        params (tuple[Any, ...] | None, optional): The parameters to be passed. Defaults to None.

    Returns:
        list[dict[str, Any]]: A list containing the fetched rows.
    """

    async def _fetchall(conn: aiosqlite.Connection) -> list[dict[str, Any]] | None:
        try:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows] if rows else None
        except:
            await conn.rollback()
            raise

    return await _run(_fetchall)


async def initialize_tables() -> None:
    """This function is used to initiate the new database tables."""

    async def _initialize_tables(conn: aiosqlite.Connection) -> None:
        try:
            # executes every table query
            for table in TABLES:
                await conn.execute(table)
            await conn.commit()  # commits all
        except:
            await conn.rollback()
            raise

    return await _run(_initialize_tables)
