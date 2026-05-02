import aiomysql
import datetime
from src.utils.loadConfig import mysqlInfo

def withConnection(func):
    async def wrapper(*args, **kwargs):
        connection = await aiomysql.connect(
            host=mysqlInfo["host"],
            port=mysqlInfo["port"],
            user=mysqlInfo["user"],
            password=mysqlInfo["password"],
            db=mysqlInfo["database"]
        )
        try:
            cursor = await connection.cursor()
            result = await func(cursor, *args, **kwargs)
            await connection.commit()
            return result
        except Exception as e:
            await connection.rollback()
            print(e)
            return False
        finally:
            cursor.close()
            connection.close()
    return wrapper

@withConnection
async def createTables(cursor: aiomysql.Cursor) -> bool:
    await cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        discordID BIGINT PRIMARY KEY,
        minecraftUsername TEXT NOT NULL,
        minecraftUUID TEXT NOT NULL,
        tier TEXT NOT NULL,
        lastTest INT NOT NULL,
        server TEXT NOT NULL,
        gamemode TEXT NOT NULL,
        region TEXT NOT NULL,
        restricted BOOLEAN NOT NULL,
        verified BOOLEAN NOT NULL DEFAULT 0,
        verification_date INT NOT NULL DEFAULT 0
    )""")
    return True

@withConnection
async def addUser(cursor: aiomysql.Cursor, discordID: int, minecraftUsername: str, minecraftUUID: str, 
                  tier: str, lastTest: int, server: str, gamemode: str, region: str, verified: bool = True) -> bool:
    verification_date = int(datetime.datetime.now().timestamp()) if verified else 0
    await cursor.execute("""
    INSERT INTO users (discordID, minecraftUsername, minecraftUUID, tier, lastTest, server, gamemode, region, restricted, verified, verification_date)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        minecraftUsername = VALUES(minecraftUsername),
        minecraftUUID = VALUES(minecraftUUID),
        server = VALUES(server),
        gamemode = VALUES(gamemode),
        region = VALUES(region),
        verified = VALUES(verified),
        verification_date = VALUES(verification_date)
    """, (discordID, minecraftUsername, minecraftUUID, tier, lastTest, server, gamemode, region, False, verified, verification_date))
    return True

@withConnection
async def getUserTicket(cursor: aiomysql.Cursor, discordID: int):
    await cursor.execute("""
    SELECT minecraftUsername, tier, server, minecraftUUID FROM users WHERE discordID = %s
    """, (discordID,))

    return await cursor.fetchone()


@withConnection
async def getResultInfo(cursor: aiomysql.Cursor, discordID: int):
    await cursor.execute("""
    SELECT minecraftUsername, tier, gamemode FROM users WHERE discordID = %s
    """, (discordID,))

    return await cursor.fetchone()


@withConnection
async def addResult(cursor: aiomysql.Cursor, discordID: int, tier: str) -> bool:
    lastTest = int(datetime.datetime.now().timestamp())
    await cursor.execute("""
    UPDATE users
        SET tier = %s, lastTest = %s
    WHERE
        discordID = %s    
    """, (tier, lastTest, discordID))
    return True

@withConnection
async def userExists(cursor: aiomysql.Cursor, discordID: int) -> bool:
    await cursor.execute("SELECT 1 FROM users WHERE discordID = %s LIMIT 1", (discordID,))
    return await cursor.fetchone() is not None

@withConnection
async def getLastTest(cursor: aiomysql.Cursor, discordID: int):
    await cursor.execute("SELECT lastTest FROM users WHERE discordID = %s", (discordID,))
    return await cursor.fetchone()

@withConnection
async def getTier(cursor: aiomysql.Cursor, discordID: int):
    await cursor.execute("SELECT tier FROM users WHERE discordID = %s", (discordID,))
    return await cursor.fetchone()

@withConnection
async def isRestricted(cursor: aiomysql.Cursor, discordID: int) -> bool:
    await cursor.execute("SELECT restricted FROM users WHERE discordID = %s", (discordID,))
    result = await cursor.fetchone()
    return result[0] if result else False

@withConnection
async def updateUsername(cursor: aiomysql.Cursor, discordID: int, username: str, uuid: int) -> bool:
    await cursor.execute("""
    UPDATE users
        SET minecraftUsername = %s, minecraftUUID = %s
    WHERE
        discordID = %s    
    """, (username, uuid, discordID))
    return True

@withConnection
async def updateTier(cursor: aiomysql.Cursor, discordID: int, tier: str) -> bool:
    await cursor.execute("""
    UPDATE users
        SET tier = %s
    WHERE
        discordID = %s    
    """, (tier, discordID))
    return True

@withConnection
async def updateRestriction(cursor: aiomysql.Cursor, discordID: int, restricted: bool) -> bool:
    await cursor.execute("""
    UPDATE users
        SET restricted = %s
    WHERE
        discordID = %s    
    """, (restricted, discordID))
    return True

@withConnection
async def getUserInfo(cursor: aiomysql.Cursor, discordID: int):
    await cursor.execute("""
    SELECT minecraftUsername, tier, lastTest, gamemode, restricted, minecraftUUID 
    FROM users WHERE discordID = %s
    """, (discordID,))
    return await cursor.fetchone()

@withConnection
async def isVerified(cursor: aiomysql.Cursor, discordID: int) -> bool:
    await cursor.execute("SELECT verified FROM users WHERE discordID = %s", (discordID,))
    result = await cursor.fetchone()
    return bool(result[0]) if result else False

@withConnection
async def getUserGamemode(cursor: aiomysql.Cursor, discordID: int):
    await cursor.execute("SELECT gamemode FROM users WHERE discordID = %s", (discordID,))
    result = await cursor.fetchone()
    return result[0] if result else None
