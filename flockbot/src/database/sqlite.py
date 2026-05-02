import sqlite3
import datetime

def withConnection(func):
    async def wrapper(*args, **kwargs):
        connection = sqlite3.connect('storage/database.db')
        try:
            cursor = connection.cursor()
            result = await func(cursor, *args, **kwargs)
            connection.commit()
            return result
        except Exception as e:
            connection.rollback()
            print(e)
            return False
        finally:
            connection.close()
    return wrapper

@withConnection
async def createTables(cursor: sqlite3.Cursor) -> bool:
    # Check if old table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    old_table_exists = cursor.fetchone()
    
    if old_table_exists:
        # Check if old table has the old structure (discordID as primary key)
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        has_old_structure = any(col[1] == 'discordID' and col[5] == 1 for col in columns)  # col[5] is pk
        
        if has_old_structure and not any(col[1] == 'gamemode' and col[5] == 1 for col in columns):
            # Old structure: rename table and create new one
            cursor.execute("ALTER TABLE users RENAME TO users_old")
            
            # Create new table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                discordID INTEGER NOT NULL,
                gamemode TEXT NOT NULL,
                minecraftUsername TEXT NOT NULL,
                minecraftUUID TEXT NOT NULL,
                tier TEXT NOT NULL,
                lastTest INTEGER NOT NULL,
                server TEXT NOT NULL,
                region TEXT NOT NULL,
                restricted BOOLEAN NOT NULL,
                verified BOOLEAN NOT NULL DEFAULT 0,
                verification_date INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (discordID, gamemode)
            )""")
            
            # Migrate data: for each old user, create entries for all gamemodes they were verified for
            # But since old had one gamemode, copy as is
            cursor.execute("""
            INSERT INTO users (discordID, gamemode, minecraftUsername, minecraftUUID, tier, lastTest, server, region, restricted, verified, verification_date)
            SELECT discordID, gamemode, minecraftUsername, minecraftUUID, tier, lastTest, server, region, restricted, verified, verification_date
            FROM users_old
            """)
            
            # Drop old table
            cursor.execute("DROP TABLE users_old")
            print("Migrated old database structure to new multi-gamemode format")
        else:
            # New structure already exists or no old table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                discordID INTEGER NOT NULL,
                gamemode TEXT NOT NULL,
                minecraftUsername TEXT NOT NULL,
                minecraftUUID TEXT NOT NULL,
                tier TEXT NOT NULL,
                lastTest INTEGER NOT NULL,
                server TEXT NOT NULL,
                region TEXT NOT NULL,
                restricted BOOLEAN NOT NULL,
                verified BOOLEAN NOT NULL DEFAULT 0,
                verification_date INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (discordID, gamemode)
            )""")
    else:
        # No old table, create new
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            discordID INTEGER NOT NULL,
            gamemode TEXT NOT NULL,
            minecraftUsername TEXT NOT NULL,
            minecraftUUID TEXT NOT NULL,
            tier TEXT NOT NULL,
            lastTest INTEGER NOT NULL,
            server TEXT NOT NULL,
            region TEXT NOT NULL,
            restricted BOOLEAN NOT NULL,
            verified BOOLEAN NOT NULL DEFAULT 0,
            verification_date INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (discordID, gamemode)
        )""")
    
    return True

@withConnection
async def addUser(cursor: sqlite3.Cursor, discordID: int, minecraftUsername: str, minecraftUUID: str, 
                  tier: str, lastTest: int, server: str, gamemode: str, region: str, verified: bool = True) -> bool:
    verification_date = int(datetime.datetime.now().timestamp()) if verified else 0
    cursor.execute("""
    INSERT OR REPLACE INTO users (discordID, gamemode, minecraftUsername, minecraftUUID, tier, lastTest, server, region, restricted, verified, verification_date)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (discordID, gamemode, minecraftUsername, minecraftUUID, tier, lastTest, server, region, False, verified, verification_date))
    return True

@withConnection
async def getUserTicket(cursor: sqlite3.Cursor, discordID: int, gamemode: str):
    cursor.execute("""
    SELECT minecraftUsername, tier, server, minecraftUUID FROM users WHERE discordID = ? AND gamemode = ?
    """, (discordID, gamemode))
    return cursor.fetchone()


@withConnection
async def getResultInfo(cursor: sqlite3.Cursor, discordID: int, gamemode: str):
    cursor.execute("""
    SELECT minecraftUsername, tier, gamemode FROM users WHERE discordID = ? AND gamemode = ?
    """, (discordID, gamemode))
    return cursor.fetchone()


@withConnection
async def addResult(cursor: sqlite3.Cursor, discordID: int, tier: str, gamemode: str) -> bool:
    lastTest = int(datetime.datetime.now().timestamp())
    cursor.execute("""
    UPDATE users
        SET tier = ?, lastTest = ?
    WHERE
        discordID = ? AND gamemode = ?
    """, (tier, lastTest, discordID, gamemode))

@withConnection
async def userExists(cursor: sqlite3.Cursor, discordID: int) -> bool:
    cursor.execute("SELECT 1 FROM users WHERE discordID = ? LIMIT 1", (discordID,))
    return cursor.fetchone() is not None

@withConnection
async def getLastTest(cursor: sqlite3.Cursor, discordID: int):
    cursor.execute("SELECT lastTest FROM users WHERE discordID = ?", (discordID,))
    return cursor.fetchone()

@withConnection
async def getTier(cursor: sqlite3.Cursor, discordID: int):
    cursor.execute("SELECT tier FROM users WHERE discordID = ?", (discordID,))
    return cursor.fetchone()

@withConnection
async def isRestricted(cursor: sqlite3.Cursor, discordID: int) -> bool:
    cursor.execute("SELECT restricted FROM users WHERE discordID = ?", (discordID,))
    result = cursor.fetchone()
    return result[0] if result else False

@withConnection
async def updateUsername(cursor: sqlite3.Cursor, discordID: int, username: str, uuid: int) -> bool:
    cursor.execute("""
    UPDATE users
        SET minecraftUsername = ?, minecraftUUID = ?
    WHERE
        discordID = ?    
    """, (username, uuid, discordID))
    return True

@withConnection
async def updateTier(cursor: sqlite3.Cursor, discordID: int, tier: str) -> bool:
    cursor.execute("""
    UPDATE users
        SET tier = ?
    WHERE
        discordID = ?    
    """, (tier, discordID))
    return True

@withConnection
async def updateRestriction(cursor: sqlite3.Cursor, discordID: int, restricted: bool) -> bool:
    cursor.execute("""
    UPDATE users
        SET restricted = ?
    WHERE
        discordID = ?    
    """, (restricted, discordID))
    return True

@withConnection
async def getUserInfo(cursor: sqlite3.Cursor, discordID: int):
    cursor.execute("""
    SELECT minecraftUsername, tier, lastTest, gamemode, restricted, minecraftUUID 
    FROM users WHERE discordID = ?
    """, (discordID,))
    return cursor.fetchone()

@withConnection
async def isVerified(cursor: sqlite3.Cursor, discordID: int, gamemode: str = None) -> bool:
    if gamemode:
        cursor.execute("SELECT verified FROM users WHERE discordID = ? AND gamemode = ?", (discordID, gamemode))
    else:
        cursor.execute("SELECT verified FROM users WHERE discordID = ? LIMIT 1", (discordID,))
    result = cursor.fetchone()
    return bool(result[0]) if result else False

@withConnection
async def getUserGamemode(cursor: sqlite3.Cursor, discordID: int):
    cursor.execute("SELECT gamemode FROM users WHERE discordID = ?", (discordID,))
    results = cursor.fetchall()
    return [row[0] for row in results] if results else []
