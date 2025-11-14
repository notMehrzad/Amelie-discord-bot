import aiosqlite

#connection helper function
async def connection():
    connection = await aiosqlite.connect("bot_database.db") #connects to the db file
    await connection.execute("PRAGMA foreign_keys = ON;")
    return connection

#setups the db helper function
async def setup():
    async with await connection() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS warns (
            warn_id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id INTEGER NOT NULL,
            mod_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        await conn.commit()