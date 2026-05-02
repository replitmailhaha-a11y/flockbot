from src.utils.loadConfig import databaseType

if databaseType == "mysql":
    from src.database import mysql as db
elif databaseType == "sqlite":
    from src.database import sqlite as db
else:
    raise ValueError(f"Unsupported database type: {databaseType}")

async def createTables() -> bool:
    return await db.createTables()

async def addUser(discordID: int, minecraftUsername: str, minecraftUUID: str,
                  tier: str, lastTest: int, server: str, gamemode: str, region: str, verified: bool = True) -> bool:
    return await db.addUser(discordID, minecraftUsername, minecraftUUID, tier, lastTest, server, gamemode, region, verified)

async def getUserTicket(discordID: int, gamemode: str):
    return await db.getUserTicket(discordID, gamemode)

async def getResultInfo(discordID: int, gamemode: str):
    return await db.getResultInfo(discordID, gamemode)

async def addResult(discordID: int, tier: str, gamemode: str) -> bool:
    return await db.addResult(discordID, tier, gamemode)

async def userExists(discordID: int) -> bool:
    return await db.userExists(discordID)

async def getLastTest(discordID: int):
    return await db.getLastTest(discordID)

async def getTier(discordID: int):
    return await db.getTier(discordID)

async def updateUsername(discordID: int, username: str, uuid: str) -> bool:
    return await db.updateUsername(discordID, username, uuid)

async def updateTier(discordID: int, tier: str) -> bool:
    return await db.updateTier(discordID, tier)

async def isRestriced(discordID: int) -> bool:
    return await db.isRestricted(discordID=discordID)

async def updateRestriction(discordID: int, restricted: bool) -> bool:
    return await db.updateRestriction(discordID=discordID, restricted=restricted)

async def getUserInfo(discordID: int):
    return await db.getUserInfo(discordID=discordID)

async def isVerified(discordID: int, gamemode: str = None) -> bool:
    return await db.isVerified(discordID, gamemode)

async def getUserGamemode(discordID: int):
    return await db.getUserGamemode(discordID)
