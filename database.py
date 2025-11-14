import aiosqlite

#connection helper function
async def connection():
    conn = await aiosqlite.connect("bot_database.db") #connects to the db file
    await conn.execute("PRAGMA foreign_keys = ON;")
    return conn

#setups the db helper function
async def setup():
    conn = await connection()

    #warns table
    await conn.execute("""
    CREATE TABLE IF NOT EXISTS warns (
        warn_id INTEGER PRIMARY KEY AUTOINCREMENT,
        server_id INTEGER NOT NULL,
        warn_number INTEGER NOT NULL,
        mod_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        reason TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    await conn.commit() #commits the changes
    await conn.close()