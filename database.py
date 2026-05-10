import aiosqlite
import discord
from typing import Any, Iterable
from discord.ext import commands
from enum import Enum
from contextlib import asynccontextmanager


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


class Database:
    db_path = "bot_database.db"

    @asynccontextmanager
    async def _connect(self, db_path: str = db_path):
        async with aiosqlite.connect(db_path) as conn:  # connects to the db file
            await conn.execute("PRAGMA foreign_keys = ON;")
            conn.row_factory = aiosqlite.Row
            try:
                yield conn
            except:
                await conn.rollback()
                raise

    async def execute(self, query: str, params: Iterable[Any] | None = None):
        async with self._connect() as conn:
            async with conn.execute(query, params) as cursor:
                await conn.commit()
                return cursor

    async def fetchone(self, query: str, params: Iterable[Any] | None = None):
        async with self._connect() as conn:
            async with conn.execute(query, params) as cursor:
                return await cursor.fetchone()

    async def fetchall(self, query: str, params: Iterable[Any] | None = None):
        async with self._connect() as conn:
            async with conn.execute(query, params) as cursor:
                return await cursor.fetchall()

    # setups the db helper function
    async def tableInitialize(self):
        tables = [
            # warns table
            """
            CREATE TABLE IF NOT EXISTS warns (
                warn_id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_id INTEGER NOT NULL,
                user_warn_id INTEGER NOT NULL,
                mod_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                reason TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """,
            # anon users table
            """
            CREATE TABLE IF NOT EXISTS anonusers (
                user_id INTEGER PRIMARY KEY NOT NULL,
                public_id TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """,
            # anon user contact table
            """
            CREATE TABLE IF NOT EXISTS anonusercontact (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                contact_id INTEGER NOT NULL,
                contact_anon_id TEXT NOT NULL,
                blocked INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES anonusers(user_id),
                UNIQUE(user_id, contact_id),
                UNIQUE(user_id, contact_anon_id)
            );
            """,
            # anon session table
            """
            CREATE TABLE IF NOT EXISTS anonsessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                reciever_id INTEGER NOT NULL,
                contact_anon_id TEXT NOT NULL,
                contact_message_collector_id INTEGER NOT NULL,
                session_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                responded INTEGER DEFAULT 0,
                FOREIGN KEY (reciever_id) REFERENCES anonusers(user_id),
                UNIQUE(reciever_id, contact_anon_id, session_id)
            );
            """,
            # bank accounts table
            """
            CREATE TABLE IF NOT EXISTS bank_accounts (
                user_id INTEGER PRIMARY KEY NOT NULL,
                balance INTEGER NOT NULL,
                created_at INTEGER NOT NULL,
                last_daily_date INTEGER,
                last_work_date INTEGER
            );
            """,
            # bank transactions table
            """
            CREATE TABLE IF NOT EXISTS bank_transactions (
                transaction_id TEXT PRIMARY KEY NOT NULL,
                type TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                date INTEGER NOT NULL,
                reciever_id INTEGER
            );
            """,
            # inventory table
            """
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_name str NOT NULL,
                quantity int NOT NULL,
                FOREIGN KEY (user_id) REFERENCES user(user_id)
            );
            """,
            # tickets table
            """
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message_collector_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                state TEXT NOT NULL DEFAULT "open",
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                closed_at DATETIME
            );
            """,
            # lottery table
            """
            CREATE TABLE IF NOT EXISTS lottery (
                user_id INTEGER PRIMARY KEY NOT NULL,
                signed_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """,
        ]
        async with self._connect() as conn:
            for table in tables:
                await conn.execute(table)
            await conn.commit()


db = Database()  # database instance to import
