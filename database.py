import aiosqlite
from typing import TypedDict, Any, Iterable
from contextlib import asynccontextmanager


class EconomyData(TypedDict):
    name: str
    icon: str


# economy constant datas
economyData: EconomyData = {"name": "Cookie", "icon": "<:1lvl:1027191671328354304>"}

db_path = "bot_database.db"


class Database:
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
            # anon public ids table
            """
            CREATE TABLE IF NOT EXISTS anonpublicids (
                public_id TEXT PRIMARY KEY NOT NULL,
                user_id INTEGER NOT NULL,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """,
            # anon user contact table
            """
            CREATE TABLE IF NOT EXISTS anonusercontact (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                public_id TEXT NOT NULL,
                sender_id INTEGER NOT NULL,
                sender_anon_id TEXT NOT NULL,
                blocked INTEGER DEFAULT 0,
                FOREIGN KEY (public_id) REFERENCES anonpublicids(public_id),
                UNIQUE(public_id, sender_anon_id),
                UNIQUE(public_id, sender_id)
            );
            """,
            # anon session table
            """
            CREATE TABLE IF NOT EXISTS anonsessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                reciever_id TEXT NOT NULL,
                sender_id INTEGER NOT NULL,
                sender_message_collector_id INTEGER NOT NULL,
                session_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                responded INTEGER DEFAULT 0,
                FOREIGN KEY (reciever_id) REFERENCES anonpublicids(public_id),
                UNIQUE(reciever_id, sender_id, session_id)
            );
            """,
            # user balance table
            """
            CREATE TABLE IF NOT EXISTS userbalance (
                user_id INTEGER PRIMARY KEY NOT NULL,
                balance INTEGER NOT NULL,
                last_daily_date DATETIME,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP
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
        ]
        async with self._connect() as conn:
            for table in tables:
                await conn.execute(table)
            await conn.commit()


db = Database()
