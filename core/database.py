"""Contains the logic and structure of database(aiosqlite) that Amélie uses.

It simplifies the process of executing or fetching data using a handler that manages
creating connection, commiting changes and closing connection automatically with just
simple functions.
Custom functions can be made and used like _run(CustomFunction).
"""

from __future__ import annotations

__all__ = ["execute", "fetchall", "fetchone", "initialize_tables"]

import contextlib
from enum import Enum
from typing import TYPE_CHECKING, Any, TypeVar, final

import aiosqlite

from core.dbconstants import (
    AccountTable,
    AnonContactTable,
    AnonSessionTable,
    AnonUserTable,
    CheckTable,
    InventoryTable,
    LotteryTable,
    TicketTable,
    TransactionTable,
    WarnTable,
)
from core.log_handler import logger_setup

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable
    from sqlite3 import Row

    import discord
    from discord.ext import commands

DATABASE_PATH = "bot_database.db"
TABLES: tuple[str, ...] = (
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
    CREATE TABLE IF NOT EXISTS {AnonContactTable.TABLE_NAME} (
        {AnonContactTable.COL_ID} INTEGER PRIMARY KEY AUTOINCREMENT,
        {AnonContactTable.COL_USER_ID} INTEGER NOT NULL,
        {AnonContactTable.COL_CONTACT_ID} INTEGER NOT NULL,
        {AnonContactTable.COL_CONTACT_ANON_ID} TEXT NOT NULL,
        {AnonContactTable.COL_BLOCKED} INTEGER DEFAULT 0,
        FOREIGN KEY ({AnonContactTable.COL_USER_ID}) REFERENCES
        {AnonUserTable.TABLE_NAME}({AnonUserTable.COL_USER_ID}),
        UNIQUE({AnonContactTable.COL_USER_ID}, {AnonContactTable.COL_CONTACT_ID}),
        UNIQUE({AnonContactTable.COL_USER_ID}, {AnonContactTable.COL_CONTACT_ANON_ID})
    );
    """,
    f"""
    CREATE TABLE IF NOT EXISTS {AnonSessionTable.TABLE_NAME} (
        {AnonSessionTable.COL_ID} INTEGER PRIMARY KEY AUTOINCREMENT,
        {AnonSessionTable.COL_SESSION_ID} INTEGER NOT NULL,
        {AnonSessionTable.COL_RECEIVER_ID} INTEGER NOT NULL,
        {AnonSessionTable.COL_CONTACT_ANON_ID} TEXT NOT NULL,
        {AnonSessionTable.COL_CONTACT_MESSAGE_COLLECTOR_ID} INTEGER NOT NULL,
        {AnonSessionTable.COL_SESSION_DATE} DATETIME DEFAULT CURRENT_TIMESTAMP,
        {AnonSessionTable.COL_RESPONDED} INTEGER DEFAULT 0,
        FOREIGN KEY ({AnonSessionTable.COL_RECEIVER_ID}) REFERENCES
        {AnonUserTable.TABLE_NAME}({AnonUserTable.COL_USER_ID}),
        UNIQUE({AnonSessionTable.COL_RECEIVER_ID},
        {AnonSessionTable.COL_CONTACT_ANON_ID}, {AnonSessionTable.COL_SESSION_ID})
    );
    """,
    f"""
    CREATE TABLE IF NOT EXISTS {AnonUserTable.TABLE_NAME} (
        {AnonUserTable.COL_USER_ID} INTEGER PRIMARY KEY NOT NULL,
        {AnonUserTable.COL_PUBLIC_ID} TEXT NOT NULL,
        {AnonUserTable.COL_CREATED_AT} DATETIME DEFAULT CURRENT_TIMESTAMP
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
    CREATE TABLE IF NOT EXISTS {InventoryTable.TABLE_NAME} (
        {InventoryTable.COL_USER_ID} INTEGER NOT NULL,
        {InventoryTable.COL_ITEM_NAME} TEXT NOT NULL,
        {InventoryTable.COL_QUANTITY} INTEGER NOT NULL,
        PRIMARY KEY ({InventoryTable.COL_USER_ID}, {InventoryTable.COL_ITEM_NAME})
    );
    """,
    f"""
    CREATE TABLE IF NOT EXISTS {LotteryTable.TABLE_NAME} (
        {LotteryTable.COL_USER_ID} INTEGER PRIMARY KEY NOT NULL,
        {LotteryTable.COL_SIGNED_AT} DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """,
    f"""
    CREATE TABLE IF NOT EXISTS {TicketTable.TABLE_NAME} (
        {TicketTable.COL_ID} INTEGER PRIMARY KEY AUTOINCREMENT,
        {TicketTable.COL_USER_ID} INTEGER NOT NULL,
        {TicketTable.COL_MESSAGE_COLLECTOR_ID} INTEGER NOT NULL,
        {TicketTable.COL_SUBJECT} TEXT NOT NULL,
        {TicketTable.COL_STATE} TEXT NOT NULL DEFAULT "open",
        {TicketTable.COL_CREATED_AT} DATETIME DEFAULT CURRENT_TIMESTAMP,
        {TicketTable.COL_CLOSED_AT} DATETIME
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
    f"""
    CREATE TABLE IF NOT EXISTS {WarnTable.TABLE_NAME} (
        {WarnTable.COL_ID} INTEGER PRIMARY KEY AUTOINCREMENT,
        {WarnTable.COL_SERVER_ID} INTEGER NOT NULL,
        {WarnTable.COL_USER_WARN_ID} INTEGER NOT NULL,
        {WarnTable.COL_MOD_ID} INTEGER NOT NULL,
        {WarnTable.COL_USER_ID} INTEGER NOT NULL,
        {WarnTable.COL_REASON} TEXT,
        {WarnTable.COL_TIMESTAMP} DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """,
)

T = TypeVar("T")
logger = logger_setup(__name__)


@final
class Session:
    class Types(Enum):
        GAMBLING = "GAMBLING"
        MESSAGING = "MESSAGING"

    sessions: dict[tuple[int, Types], Session] = {}  # noqa: RUF012

    def __init__(self, user_id: int, session_type: Types) -> None:
        self.userId = user_id
        self.type = session_type
        self.messages = None
        Session.sessions[(self.userId, self.type)] = self

    def close(self) -> None:
        with contextlib.suppress(KeyError):
            _ = Session.sessions.pop((self.userId, self.type))

    async def collect_message(self, bot: commands.Bot, *, dm_only: bool) -> None:
        def __check(msg_: discord.Message) -> bool:
            return (
                (msg_.author.id == self.userId and not msg_.guild)
                if dm_only
                else msg_.author.id == self.userId
            )

        self.messages: list[discord.Message] | None = []
        while (self.userId, self.type) in Session.sessions:
            msg = await bot.wait_for("message", check=__check)
            self.messages.append(msg)


async def _run(func: Callable[..., Awaitable[T]]) -> T:
    """Core function to run DB commands.

    Every database function must be called inside this function to be run and executed
    properly.

    Args:
        func (Callable[..., Awaitable[T]]): Function to be run.

    Returns:
        T: Varies from function it runs to another.

    """
    # Connect to database.
    async with aiosqlite.connect(DATABASE_PATH) as conn:
        _ = await conn.execute("PRAGMA foreign_keys = ON")
        _ = await conn.execute("PRAGMA journal_mode = WAL")

        # Run the command.
        return await func(conn)


async def execute(query: str, params: Iterable[Any] | None = None) -> None:
    """Execute a SQL query in aiosqlite.

    Args:
        query (str): Query to execute.
        params (Iterable[Any] | None, optional): Parameters to pass. Defaults
            to None.

    """

    async def _execute(conn: aiosqlite.Connection) -> None:
        try:
            _ = await conn.execute(query, params)
            await conn.commit()
        except Exception:
            await conn.rollback()
            raise

    return await _run(_execute)


async def fetchone(
    query: str,
    params: Iterable[Any] | None = None,
) -> Row | None:
    """Fetch a row in aiosqlite.

    Args:
        query (str): Query to fetch.
        params (Iterable[Any, ...] | None, optional): Parameters to pass.
            Defaults to None.

    Returns:
        Row | None: Return fetched Row if it's found. `None`, otherwise.

    """

    async def _fetchone(conn: aiosqlite.Connection) -> Row | None:
        try:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(query, params) as cursor:
                return await cursor.fetchone()
        except Exception:
            await conn.rollback()
            raise

    return await _run(_fetchone)


async def fetchall(
    query: str,
    params: Iterable[Any] | None = None,
) -> Iterable[Row] | None:
    """Fetch all rows in aiosqlite.

    Args:
        query (str): Query to fetch.
        params (Iterable[Any, ...] | None, optional): Parameters to pass. Defaults to
            None.

    Returns:
        Iterable[Row]: Return An iterable containing the fetched rows.

    """

    async def _fetchall(conn: aiosqlite.Connection) -> Iterable[Row] | None:
        try:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return rows or None
        except Exception:
            await conn.rollback()
            raise

    return await _run(_fetchall)


async def initialize_tables() -> None:
    """Initialize new database tables."""

    async def _initialize_tables(conn: aiosqlite.Connection) -> None:
        try:
            # Execute every table initialization.
            for table in TABLES:
                _ = await conn.execute(table)
            # Commit changes.
            await conn.commit()
        except Exception:
            await conn.rollback()
            raise

    return await _run(_initialize_tables)
