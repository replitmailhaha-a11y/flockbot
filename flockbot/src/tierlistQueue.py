from src.utils import format
from src.utils.loadConfig import *

class TierlistQueue():
    def __init__(self, maxQueue: int, maxTesters: int, cooldown: int):

    
        self.queue = {}
        self.maxQueue = maxQueue
        self.maxTesters = maxTesters
        self.cooldown = cooldown

    def setup(self, gamemodes: dict) -> None:
        for gamemode_name, gamemode_data in gamemodes.items():
            self.queue[gamemode_name] = {
                "queueChannel": gamemode_data["queue_channel"],
                "queueMessage": None,
                "ticketCatagory": gamemode_data["ticket_catagory"],
                "pingRole": gamemode_data["role_ping"],
                "open": False,
                "testers": [],
                "queue": []
            }

    def openqueue(self, queue: str, open: bool):
        self.queue[queue]["open"] = open
        if open == False:
            self.queue[queue]["queue"] = []
            self.queue[queue]["testers"] = []

    async def addUser(self, messageID: int, userID: int):
        gamemode = ""
        for gm, data in self.queue.items():
            if data["queueMessage"] == messageID:
                gamemode = gm
                break

        if gamemode == "":
            return "gamemode doesnt exist"
        
        # Check if user is verified for this gamemode
        from src.database import databaseManager
        exists = await databaseManager.userExists(userID)
        if not exists:
            return messages["notVerified"]
        
        is_verified = await databaseManager.isVerified(userID, gamemode)
        if not is_verified:
            return messages["notVerified"]
        
        if userID in self.queue[gamemode]["queue"]:
            return messages["alreadyInQueue"]
        
        if len(self.queue[gamemode]["queue"]) >= self.maxQueue:
            return messages["queueFull"]
        
        self.queue[gamemode]["queue"].append(userID)
        return messages["addToQueue"]

    
    def removeUser(self, messageID: int, userID: int):
        gamemode = ""
        for gm, data in self.queue.items():
            if data["queueMessage"] == messageID:
                gamemode = gm
                break

        if gamemode == "":
            return "gamemode doesnt exist"
        
        if userID not in self.queue[gamemode]["queue"]:
            return messages["notInQueue"]
        
        self.queue[gamemode]["queue"].remove(userID)
        return messages["leaveQueue"]
        

    def addTester(self, gamemode: str, userID: int):
        if self.queue[gamemode]["testers"] == []:
            self.openqueue(queue=gamemode, open=True)
        
        if userID in self.queue[gamemode]["testers"]:
            return ("You are already testing this queue!", "")

        if len(self.queue[gamemode]["testers"]) < self.maxTesters:
            self.queue[gamemode]["testers"].append(userID)
            return (f"{messages["testerOpenQueue"]}: <#{listGamemodes[gamemode]["queue_channel"]}>", self.makeQueueMessage(gamemode=gamemode))
        
    def removeTester(self, gamemode: str, userID: str):
        if self.queue[gamemode]["open"] == False: return "Testing is closed"

        if userID in self.queue[gamemode]["testers"]:
            self.queue[gamemode]["testers"].remove(userID)
            
            if self.queue[gamemode]["testers"] == []:
                self.openqueue(queue=gamemode, open=False)
                return ("testing has closed", format.formatnoqueue(), self.queue[gamemode]["queueChannel"], self.queue[gamemode]["queueMessage"])

            return ("you have stopped testing", self.makeQueueMessage(gamemode=gamemode), self.queue[gamemode]["queueChannel"], self.queue[gamemode]["queueMessage"])
        
        return ("you are not testing this gamemode", self.makeQueueMessage(gamemode=gamemode), self.queue[gamemode]["queueChannel"], self.queue[gamemode]["queueMessage"])
    
    def getNextTest(self, testerID: int, gamemode: str):
        if self.queue[gamemode]["queue"] == []:
            return (None, f"No users are in the queue for the {gamemode} gamemode")
        user = self.queue[gamemode]["queue"].pop(0)
        return (user, None)

        
    def makeQueueMessage(self, gamemode: str):
        capacity = f"{len(self.queue[gamemode]["queue"])}/{self.maxQueue}"
        testerCapacity = f"{len(self.queue[gamemode]["testers"])}/{self.maxTesters}"
        queue = "\n".join([f"{i+1}. <@{user_id}>" for i, user_id in enumerate(self.queue[gamemode]["queue"])])
        testers = "\n".join([f"{i+1}. <@{user_id}>" for i, user_id in enumerate(self.queue[gamemode]["testers"])])

        return format.formatqueue(capacity=capacity, queue=queue, testerCapacity=testerCapacity, testers=testers, gamemode=gamemode)

    def addQueueMessageId(self, gamemode: str, messageID: int):
        self.queue[gamemode]["queueMessage"] = messageID
    
    def getqueueraw(self) -> dict:
        return self.queue
