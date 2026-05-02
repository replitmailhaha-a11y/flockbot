import yaml
import logging  
import sys

try:
    with open("config/config.yml", "r") as file:
        config = yaml.safe_load(file)
except Exception as e:
    logging.exception("Failed to load configuration file:")
    sys.exit("Error: Unable to load config file.")

try:
    catagories = config["bot"]["catagories"]
    
    # Global tiers (fallback)
    listTiers: list[str] = [key for key in config["bot"]["tiers"]]; listTiers.append("none")
    listHighTiers: list[str] = config["bot"]["highTiers"]
    listGamemodesText: list[str] = [key for key in config["bot"]["gamemodes"]]
    listGamemodeCategories: list[int] = [gm["ticket_catagory"] for gm in config["bot"]["gamemodes"].values()]
    listGamemodeCategories.append(catagories["highTests"])
    listGamemodeQueueChannel: list[int] = [gm["queue_channel"] for gm in config["bot"]["gamemodes"].values()]
    listGamemodeRolePing: list[int] = [gm["role_ping"] for gm in config["bot"]["gamemodes"].values()]
    listGamemodeQueueRole: list[int] = [gm["queue_role"] for gm in config["bot"]["gamemodes"].values()]
    listGamemodeTesterRole: list[int] = [gm["tester_role"] for gm in config["bot"]["gamemodes"].values()]

    verifiedRole: int = config["bot"]["roles"]["verified"]

    # Global tier roles (fallback)
    listTierRoles: dict[str, int] = {tier: role_id for tier, role_id in config["bot"]["tiers"].items()}
    
    # Per-gamemode tier roles
    gamemodeTiers: dict[str, dict[str, int]] = {}
    for gm_name, gm_data in config["bot"]["gamemodes"].items():
        if "tiers" in gm_data:
            gamemodeTiers[gm_name] = {tier: role_id for tier, role_id in gm_data["tiers"].items()}

    messages = config["bot"]["messages"]

    listGamemodes = config["bot"]["gamemodes"]

    maxQueue = config["bot"]["options"]["queueLimit"]
    maxTester = config["bot"]["options"]["testerLimit"]
    cooldown = config["bot"]["options"]["cooldown"]
    reloadQueue = config["bot"]["options"]["reloadQueue"]

    channels = config["bot"]["channels"]

    mysqlInfo = config["database"]["mysql"]
    databaseType = config["database"]["type"]
    
except Exception as e:
    logging.exception(f"Setting up config failed:")
    sys.exit("Error: Failed to setup config")
