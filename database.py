import aiosqlite

#connection helper function
async def connection():
    """
    Makes a connection to the database.
    """

    conn = await aiosqlite.connect("bot_database.db") #connects to the db file
    await conn.execute("PRAGMA foreign_keys = ON;")
    return conn

#setups the db helper function
async def setup():
    """
    Sets up the initial database tables.
    """

    conn = await connection()

    #warns table
    await conn.execute("""
    CREATE TABLE IF NOT EXISTS warns (
        warn_id INTEGER PRIMARY KEY AUTOINCREMENT,
        server_id INTEGER NOT NULL,
        user_warn_id INTEGER NOT NULL,
        mod_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        reason TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    #anon public ids table
    await conn.execute("""
    CREATE TABLE IF NOT EXISTS anonpublicids (
        public_id TEXT PRIMARY KEY NOT NULL,
        user_id INTEGER NOT NULL,
        created_date DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    #anon user contact table
    await conn.execute("""
    CREATE TABLE IF NOT EXISTS anonusercontact (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        public_id TEXT NOT NULL,
        sender_id INTEGER NOT NULL,
        sender_anon_id TEXT NOT NULL,
        FOREIGN KEY (public_id) REFERENCES anonpublicids(public_id),
        UNIQUE(public_id, sender_anon_id),
        UNIQUE(public_id, sender_id)
    );
    """)

    #anon session table
    await conn.execute("""
    CREATE TABLE IF NOT EXISTS anonsessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        reciever_id TEXT NOT NULL,
        sender_id INTEGER NOT NULL,
        sender_message_channel_id INTEGER NOT NULL,
        sender_message_collector_id INTEGER NOT NULL,
        session_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        responded INTEGER DEFAULT 0,
        FOREIGN KEY (reciever_id) REFERENCES anonpublicids(public_id),
        UNIQUE(reciever_id, sender_id, session_id)
    );
    """)

    await conn.commit() #commits the changes
    await conn.close()