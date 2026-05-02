import os
import sys
import logging
import time
import asyncio

import nextcord
from nextcord.ext import commands, tasks
from dotenv import load_dotenv

from src.utils import mojang, format, permissions
from src.tierlistQueue import TierlistQueue
from src.ui.enterQueueButton import EnterQueueButton
from src.ui.closeTicketButton import CloseTicketButton
from src.ui.gamemodeSelect import GamemodeSelect
from src.database import databaseManager
from src.utils.loadConfig import *

# Import keep_alive for hosting platforms
try:
    from keep_alive import start
    HOSTING_ENABLED = True
except ImportError:
    HOSTING_ENABLED = False

try:
    os.makedirs("logs", exist_ok=True)
    os.makedirs("storage", exist_ok=True)
except Exception as e:
    print(f"Unable to create logs/storage directory: ", e)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(name)s: %(message)s",
    handlers=[
        logging.FileHandler(f"logs/logs-{time.time()}.log")
    ]
)

load_dotenv()

intents = nextcord.Intents.all()
bot = commands.Bot(intents=intents)


try:
    queue = TierlistQueue(maxQueue=maxQueue, maxTesters=maxTester, cooldown=cooldown)
    queue.setup(listGamemodes)

except Exception as e:
    logging.exception(f"Setting up queue failed:")
    sys.exit("Error: Failed to setup queue")

def is_me(m):
    return m.author == bot.user

async def setupBot():
    await databaseManager.createTables()
    
    # Setup channel permissions for all gamemodes
    guild = None
    for guild in bot.guilds:
        break
    
    if guild:
        await permissions.setup_gamemode_channel_permissions(guild, listGamemodes)
        logging.info("Setup gamemode channel permissions")

    # Post gamemode selection message in welcome channel
    welcome_channel = bot.get_channel(channels["welcome"])
    if welcome_channel is None:
        logging.error(f"Welcome channel not found: {channels['welcome']}")
        sys.exit("Failed startup sequence - welcome channel not found")
    
    # Clear old messages from bot
    await welcome_channel.purge(limit=10, check=is_me)
    
    # Create welcome embed
    welcome_embed = nextcord.Embed(
        title="🎮 Welcome to Tier Testing!",
        description="Select your gamemode from the dropdown below to get started with verification.\n\n"
                    "**How it works:**\n"
                    "1. Choose your gamemode from the dropdown\n"
                    "2. Enter your Minecraft username and details\n"
                    "3. Get verified and access your queue channel\n"
                    "4. Join the queue and get tested!\n\n"
                    "**Note:** You can verify for multiple gamemodes by selecting them one at a time.",
        color=nextcord.Color.blue()
    )
    welcome_embed.add_field(
        name="Available Gamemodes",
        value="• mace\n"
              "• nethpot\n"
              "• smp\n"
              "• sword\n"
              "• uhc\n"
              "• axe\n"
              "• diamondpot\n"
              "• vanilla",
        inline=False
    )
    welcome_embed.add_field(
        name="⚠️ Important",
        value="You must provide authentic information. Failure to do so will result in a denied test.",
        inline=False
    )
    
    await welcome_channel.send(
        embed=welcome_embed,
        view=GamemodeSelect()
    )
    logging.info("Posted gamemode selection message in welcome channel")

    # Setup queue messages for each gamemode
    for gamemode in listGamemodes:
        ch = bot.get_channel(listGamemodes[gamemode]["queue_channel"])
        if ch is None:
            logging.warning(f"queue_channel for gamemode '{gamemode}' not found: {listGamemodes[gamemode]['queue_channel']} - skipping")
            continue
        if not isinstance(ch, nextcord.TextChannel):
            logging.warning(f"queue_channel for gamemode '{gamemode}' is not a TextChannel - skipping")
            continue
        
        await ch.purge(limit=10, check=is_me)
        await ch.send(embed=nextcord.Embed.from_dict(format.formatnoqueue(gamemode=gamemode)))
    
    logging.info("Bot setup complete")


@bot.event
async def on_ready():
    print(f"Unified Tier Testing bot has logged online ✅")
    print(f"Managing {len(listGamemodes)} gamemodes: {', '.join(listGamemodes.keys())}")
    try:
        await setupBot()
        updateQueue.start()
    except Exception as e:
        logging.exception("Failed bot startup sequence: ")
        sys.exit("Failed startup sequence")

@tasks.loop(seconds=reloadQueue)
async def updateQueue():
    queues = queue.getqueueraw()
    for gamemode, data in queues.items():
        if not data["open"]:
            continue

        messageID = data["queueMessage"]
        if messageID == None:
            continue
        channel = bot.get_channel(data["queueChannel"])
        message: nextcord.Message = await channel.fetch_message(messageID)
        messageUpdate = queue.makeQueueMessage(gamemode=gamemode)
        await message.edit(embed=nextcord.Embed.from_dict(messageUpdate))


@bot.slash_command(name="results", description="closes a ticket and gives a tier to a user")
async def results(
    interaction: nextcord.Interaction,
    user: nextcord.User = nextcord.SlashOption(
        description="Enter their discord account",
        required=True,
    ),
    gamemode: str = nextcord.SlashOption(
        description="Select the gamemode",
        required=True,
        choices=listGamemodesText
    ),
    newtier: str = nextcord.SlashOption(
        description="Enter their new tier",
        required=True,
        choices=listTiers
    )
    ):
    try:
        # Check if user has tester role for this specific gamemode
        gamemode_tester_role = listGamemodes[gamemode].get("tester_role")
        if not gamemode_tester_role:
            await interaction.response.send_message("Tester role not configured for this gamemode", ephemeral=True)
            return
        
        if gamemode_tester_role not in [role.id for role in interaction.user.roles]: 
            await interaction.response.send_message(messages["noPermission"], ephemeral=True)
            return
        
        # Check if user is in database (they must be verified first)
        exists = await databaseManager.userExists(user.id)
        
        if not exists:
            await interaction.response.send_message(
                f"User {user.mention} is not verified. They must verify via the welcome menu first!",
                ephemeral=True
            )
            return

        # Check for restrictions
        isrestricted = await databaseManager.isRestriced(interaction.user.id)
        if isrestricted: 
            await interaction.response.send_message(content="You are currently restricted from using this command", ephemeral=True)
            return

        restricted = await databaseManager.isRestriced(user.id)
        if restricted: 
            await interaction.response.send_message(f"User {user.mention} is restricted", ephemeral=True)
            return

        # Get info from database (ignoring provided minecraft_username if they are already registered)
        result_info = await databaseManager.getResultInfo(user.id, gamemode)
        
        if not result_info:
            await interaction.response.send_message(
                f"User {user.mention} is not verified for {gamemode}.",
                ephemeral=True
            )
            return
        
        username, oldtier, user_gamemode = result_info
        
        uuid = await mojang.getuserid(username=username)
        discord_name = user.name
        user_id = user.id

        result_embed_data = format.formatresult(
            discordUsername=discord_name, 
            testerID=interaction.user.id, 
            gamemode=gamemode, 
            minecraftUsername=username, 
            oldTier=oldtier, 
            newTier=newtier, 
            uuid=uuid
        )
        embed = nextcord.Embed.from_dict(result_embed_data)

        # Update database with new tier
        await databaseManager.addResult(discordID=user_id, tier=newtier, gamemode=gamemode)

        member = interaction.guild.get_member(user_id)
        if member:
            gamemode_roles_to_remove = [role for role in member.roles if role.id in listGamemodeRolePing]
            if gamemode_roles_to_remove:
                await member.remove_roles(*gamemode_roles_to_remove, reason="Gamemode roles removed by /results command")

            # Get tier roles for this specific gamemode
            gamemode_tier_roles = gamemodeTiers.get(gamemode, listTierRoles)
            tier_roles_to_remove = [role for role in member.roles if role.id in gamemode_tier_roles.values()]
            if tier_roles_to_remove:
                await member.remove_roles(*tier_roles_to_remove, reason="Old tier roles removed by /results command")
            
            # Assign new tier role from gamemode-specific tiers
            if newtier != "none" and newtier in gamemode_tier_roles:
                new_tier_role = interaction.guild.get_role(gamemode_tier_roles[newtier])
                if new_tier_role:
                    await member.add_roles(new_tier_role, reason=f"New {gamemode} tier role added by /results command")

        await bot.get_channel(channels["results"]).send(content=f"<@{user_id}>", embed=embed)
        await interaction.response.send_message(content=messages["resultMessageSent"], ephemeral=True)
    except Exception as e:
        logging.exception("Error in /results command:")
        await interaction.response.send_message(content=messages["error"], ephemeral=True)

@bot.slash_command(name="openqueue", description="opens a queue in a set gamemode")
async def openqueue(
    interaction: nextcord.Interaction,
    gamemode: str = nextcord.SlashOption(
        description="Enter gamemode",
        required=True,
        choices=listGamemodesText
    )
    ):
    try:
        # Check if user has tester role for this specific gamemode
        gamemode_tester_role = listGamemodes[gamemode].get("tester_role")
        if not gamemode_tester_role:
            await interaction.response.send_message("Tester role not configured for this gamemode", ephemeral=True)
            return
        
        if gamemode_tester_role not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message(messages["noPermission"], ephemeral=True)
            return
        
        response = queue.addTester(gamemode=gamemode , userID=interaction.user.id)
        
        if response[1] != "":
            await bot.get_channel(listGamemodes[gamemode]["queue_channel"]).purge(limit=10, check=is_me)
            queueMessage: nextcord.Message = await bot.get_channel(listGamemodes[gamemode]["queue_channel"]).send(
                content=f"<@&{listGamemodes[gamemode]['role_ping']}>",
                embed=nextcord.Embed.from_dict(response[1]),
                view=EnterQueueButton(queue=queue)
            )
            queue.addQueueMessageId(gamemode=gamemode, messageID=queueMessage.id)
        await interaction.response.send_message(content=response[0], ephemeral=True)
    except Exception as e:
        logging.exception("Error in /openqueue command:")
        await interaction.response.send_message(content=messages["error"], ephemeral=True)

@bot.slash_command(name="opentester", description="Open queue for multiple gamemodes at once")
async def opentester(
    interaction: nextcord.Interaction,
    gamemodes: str = nextcord.SlashOption(
        description="Enter gamemodes (comma-separated: mace,sword,uhc)",
        required=True
    )
):
    """
    Open queue for multiple gamemodes at once
    Usage: /opentester gamemodes:mace,sword,uhc
    """
    try:
        # Parse gamemodes (comma-separated)
        gamemode_list = [gm.strip().lower() for gm in gamemodes.split(",")]
        
        # Validate all gamemodes
        invalid_gamemodes = [gm for gm in gamemode_list if gm not in listGamemodes]
        if invalid_gamemodes:
            await interaction.response.send_message(
                f"Invalid gamemodes: {', '.join(invalid_gamemodes)}\nAvailable: {', '.join(listGamemodes.keys())}",
                ephemeral=True
            )
            return
        
        # Check if user has tester roles for ANY of the gamemodes
        opened_gamemodes = []
        failed_gamemodes = []
        
        for gamemode in gamemode_list:
            # Check if user has tester role for this specific gamemode
            gamemode_tester_role = listGamemodes[gamemode].get("tester_role")
            if not gamemode_tester_role:
                failed_gamemodes.append(f"{gamemode} (no tester role configured)")
                continue
            
            if gamemode_tester_role not in [role.id for role in interaction.user.roles]:
                failed_gamemodes.append(f"{gamemode} (no permission)")
                continue
            
            # Add tester to queue
            response = queue.addTester(gamemode=gamemode, userID=interaction.user.id)
            
            if response[1] != "":
                # Send queue message
                await bot.get_channel(listGamemodes[gamemode]["queue_channel"]).purge(limit=10, check=is_me)
                queueMessage: nextcord.Message = await bot.get_channel(listGamemodes[gamemode]["queue_channel"]).send(
                    content=f"<@&{listGamemodes[gamemode]['role_ping']}>",
                    embed=nextcord.Embed.from_dict(response[1]),
                    view=EnterQueueButton(queue=queue)
                )
                queue.addQueueMessageId(gamemode=gamemode, messageID=queueMessage.id)
                opened_gamemodes.append(gamemode)
            else:
                failed_gamemodes.append(f"{gamemode} (already open)")
        
        # Build response message
        response_msg = "**Queue Status:**\n\n"
        
        if opened_gamemodes:
            response_msg += f"✅ **Opened:** {', '.join(opened_gamemodes)}\n\n"
        
        if failed_gamemodes:
            response_msg += f"❌ **Failed:**\n" + "\n".join([f"• {gm}" for gm in failed_gamemodes])
        
        await interaction.response.send_message(response_msg, ephemeral=True)
        
    except Exception as e:
        logging.exception("Error in /opentester command:")
        await interaction.response.send_message(content=messages["error"], ephemeral=True)

@bot.slash_command(name="closequeue", description="closes queue for a specific gamemode")
async def closequeue(
    interaction: nextcord.Interaction,
    gamemode: str = nextcord.SlashOption(
        description="Enter gamemode",
        required=True,
        choices=listGamemodesText
    )
    ):
    try:
        # Check if user has tester role for this specific gamemode
        gamemode_tester_role = listGamemodes[gamemode].get("tester_role")
        if not gamemode_tester_role:
            await interaction.response.send_message("Tester role not configured for this gamemode", ephemeral=True)
            return
        
        if gamemode_tester_role not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message(messages["noPermission"], ephemeral=True)
            return
        
        response = queue.removeTester(gamemode=gamemode, userID=interaction.user.id)
        if response == "Testing is closed": 
            await interaction.response.send_message(content=response)
            return

        message_text, embed_data, channel_id, message_id = response

        queueChannel = bot.get_channel(channel_id)
        queueMessage = await queueChannel.fetch_message(message_id)

        if isinstance(embed_data, dict):
            if message_text == "testing has closed":
                await queueMessage.edit(embed=nextcord.Embed.from_dict(embed_data), view=None)
            else:
                await queueMessage.edit(embed=nextcord.Embed.from_dict(embed_data))
        else:
            logging.warning("Expected embed data to be a dict, got: %s", type(embed_data))
            await interaction.response.send_message("Something went wrong with formatting the queue embed.", ephemeral=True)
            return

        await interaction.response.send_message(content=message_text, ephemeral=True)
    except Exception as e:
        logging.exception("Error in /closequeue command:")
        await interaction.response.send_message(content=messages["error"], ephemeral=True)

@bot.slash_command(name="next", description="gets the next user you want to test")
async def next_user(
    interaction: nextcord.Interaction,
    gamemode: str = nextcord.SlashOption(
        description="Enter gamemode",
        required=True,
        choices=listGamemodesText
    )
    ):
    try:
        # Check if user has tester role for this specific gamemode
        gamemode_tester_role = listGamemodes[gamemode].get("tester_role")
        if not gamemode_tester_role:
            await interaction.response.send_message("Tester role not configured for this gamemode", ephemeral=True)
            return
        
        if gamemode_tester_role not in [role.id for role in interaction.user.roles]: 
            await interaction.response.send_message(messages["noPermission"], ephemeral=True)
            return
        
        user = queue.getNextTest(testerID=interaction.user.id, gamemode=gamemode)
        if user[0] == None: 
            await interaction.response.send_message(content=user[1], ephemeral=True)
            return

        user: nextcord.Member = await interaction.guild.fetch_member(user[0])

        channelID = await interaction.guild.create_text_channel(
            category=interaction.guild.get_channel(listGamemodes[gamemode]["ticket_catagory"]), 
            name=f"eval-{user.name}"
        )
        overwrite = nextcord.PermissionOverwrite()
        overwrite.view_channel = True
        overwrite.send_messages = True
        await channelID.set_permissions(user, overwrite=overwrite)
        
        messageData = await databaseManager.getUserTicket(user.id, gamemode)
        ticketMessage = format.formatticketmessage(
            username=messageData[0], 
            tier=messageData[1], 
            server=messageData[2], 
            uuid=messageData[3]
        )

        current_roles = user.roles
        role_ids_to_remove = [role.id for role in current_roles if role.id in [r["role_ping"] for r in listGamemodes.values()]]
        if role_ids_to_remove:
            await user.remove_roles(*[interaction.guild.get_role(role_id) for role_id in role_ids_to_remove if interaction.guild.get_role(role_id)])

        queue_channel = interaction.guild.get_channel(listGamemodes[gamemode]["queue_channel"])
        if queue_channel and isinstance(queue_channel, nextcord.TextChannel):
            await queue_channel.set_permissions(user, overwrite=None)

        await channelID.send(content=f"<@{user.id}>", embed=nextcord.Embed.from_dict(ticketMessage))
        await interaction.response.send_message(f"Ticket has been created: <#{channelID.id}>", ephemeral=True)
    except Exception as e:
        logging.exception("Error in /next command:")
        print(e)
        await interaction.response.send_message(content=messages["error"], ephemeral=True)

@bot.slash_command(name="closetest", description="closes the current test")
async def closetest(
    interaction: nextcord.Interaction,
    ):
    try:
        # Check if user has ANY tester role
        has_tester_role = False
        for gm_data in listGamemodes.values():
            tester_role = gm_data.get("tester_role")
            if tester_role and tester_role in [role.id for role in interaction.user.roles]:
                has_tester_role = True
                break
        
        if not has_tester_role: 
            await interaction.response.send_message(messages["noPermission"], ephemeral=True)
            return
        
        if (interaction.channel.category.id not in listGamemodeCategories) or interaction.channel.id in listGamemodeQueueChannel: 
            await interaction.response.send_message(content="You cannot use this command in this channel", ephemeral=True)
            return
        
        view = CloseTicketButton()

        await interaction.response.send_message("Ticket will be closed in 10 seconds", view=view)
        await asyncio.sleep(10)
        if view.cancelled == False:
            await interaction.channel.delete(reason="Ticket channel closed by command.")
    except Exception as e:
        logging.exception("Error in /closetest command:")
        await interaction.response.send_message(content=messages["error"], ephemeral=True)

@bot.slash_command(name="forceclosetest", description="closes the current test with force")
async def forceclosetest(
    interaction: nextcord.Interaction,
    ):
    try:
        # Check if user has ANY tester role
        has_tester_role = False
        for gm_data in listGamemodes.values():
            tester_role = gm_data.get("tester_role")
            if tester_role and tester_role in [role.id for role in interaction.user.roles]:
                has_tester_role = True
                break
        
        if not has_tester_role: 
            await interaction.response.send_message(messages["noPermission"], ephemeral=True)
            return
        
        if (interaction.channel.category.id not in listGamemodeCategories) or interaction.channel.id in listGamemodeQueueChannel: 
            await interaction.response.send_message(content="You cannot use this command in this channel", ephemeral=True)
            return

        await interaction.response.send_message("Ticket will be closed in 10 seconds, cannot cancel")
        await asyncio.sleep(10)
        await interaction.channel.delete(reason="Ticket channel closed by command.")
    except Exception as e:
        logging.exception("Error in /forceclosetest command:")
        await interaction.response.send_message(content=messages["error"], ephemeral=True)

@bot.slash_command(name="updateusername", description="changes a username of a user")
async def updateusername(
    interaction: nextcord.Interaction,
    user: nextcord.User = nextcord.SlashOption(
        description="Enter their discord account",
        required=True,
    ),
    username: str = nextcord.SlashOption(
        description="Enter their minecraft username",
        required=True,
    )
    ):
    try:
        # Check if user has ANY tester role
        has_tester_role = False
        for gm_data in listGamemodes.values():
            tester_role = gm_data.get("tester_role")
            if tester_role and tester_role in [role.id for role in interaction.user.roles]:
                has_tester_role = True
                break
        
        if not has_tester_role: 
            await interaction.response.send_message(content=messages["noPermission"], ephemeral=True)
            return
        
        exists = await databaseManager.userExists(user.id)
        if not exists: 
            await interaction.response.send_message("User does not exist in the database", ephemeral=True)
            return

        uuid = await mojang.getuserid(username=username)
        if uuid == "8667ba71b85a4004af54457a9734eed7": 
            await interaction.response.send_message(content="Minecraft user does not exist")
            return
        
        await databaseManager.updateUsername(discordID=user.id, username=username, uuid=uuid)
        await interaction.response.send_message(content="Username sucessfully updated", ephemeral=True)
    except Exception as e:
        logging.exception("Error in /updateusername command:")
        await interaction.response.send_message(content=messages["error"], ephemeral=True)


@bot.slash_command(name="updatetier", description="changes a tier of a user in database")
async def updatetier(
    interaction: nextcord.Interaction,
    user: nextcord.User = nextcord.SlashOption(
        description="Enter their discord account",
        required=True,
    ),
    tier: str = nextcord.SlashOption(
        description="Enter their tier",
        required=True,
        choices=listTiers
    )
    ):
    try:
        # Check if user has ANY tester role
        has_tester_role = False
        for gm_data in listGamemodes.values():
            tester_role = gm_data.get("tester_role")
            if tester_role and tester_role in [role.id for role in interaction.user.roles]:
                has_tester_role = True
                break
        
        if not has_tester_role: 
            await interaction.response.send_message(content=messages["noPermission"], ephemeral=True)
            return
        
        exists = await databaseManager.userExists(user.id)
        if not exists: 
            await interaction.response.send_message("User does not exist in the database", ephemeral=True)
            return

        await databaseManager.updateTier(discordID=user.id, tier=tier)
        await interaction.response.send_message(content="Tier sucessfully updated in database, you will need to change their roles", ephemeral=True)
    except Exception as e: 
        logging.exception("Error in /updatetier command:")
        await interaction.response.send_message(content=messages["error"], ephemeral=True)

@bot.slash_command(name="restrict", description="restrict a user")
async def restrict(
    interaction: nextcord.Interaction,
    user: nextcord.User = nextcord.SlashOption(
        description="Enter their discord account",
        required=True,
    )
    ):
    try:
        # Check if user has ANY tester role
        has_tester_role = False
        for gm_data in listGamemodes.values():
            tester_role = gm_data.get("tester_role")
            if tester_role and tester_role in [role.id for role in interaction.user.roles]:
                has_tester_role = True
                break
        
        if not has_tester_role: 
            await interaction.response.send_message(content=messages["noPermission"], ephemeral=True)
            return
        
        exists = await databaseManager.userExists(user.id)
        if not exists: 
            await interaction.response.send_message("User does not exist in the database", ephemeral=True)
            return

        await databaseManager.updateRestriction(discordID=user.id, restricted=True)

        await interaction.response.send_message(content="User has been restricted", ephemeral=True)
    except Exception as e: 
        logging.exception("Error in /restrict command:")
        await interaction.response.send_message(content=messages["error"], ephemeral=True)

@bot.slash_command(name="unrestrict", description="unrestrict a user")
async def unrestrict(
    interaction: nextcord.Interaction,
    user: nextcord.User = nextcord.SlashOption(
        description="Enter their discord account",
        required=True,
    )
    ):
    try:
        # Check if user has ANY tester role
        has_tester_role = False
        for gm_data in listGamemodes.values():
            tester_role = gm_data.get("tester_role")
            if tester_role and tester_role in [role.id for role in interaction.user.roles]:
                has_tester_role = True
                break
        
        if not has_tester_role: 
            await interaction.response.send_message(content=messages["noPermission"], ephemeral=True)
            return
        
        exists = await databaseManager.userExists(user.id)
        if not exists: 
            await interaction.response.send_message("User does not exist in the database", ephemeral=True)
            return

        await databaseManager.updateRestriction(discordID=user.id, restricted=False)

        await interaction.response.send_message(content="User has been unrestricted", ephemeral=True)
    except Exception as e: 
        logging.exception("Error in /unrestrict command:")
        await interaction.response.send_message(content=messages["error"], ephemeral=True)

@bot.slash_command(name="info", description="gathers info on a user")
async def info(
    interaction: nextcord.Interaction,
    user: nextcord.User = nextcord.SlashOption(
        description="Enter their discord account",
        required=True,
    )
    ):
    try:
        exists = await databaseManager.userExists(user.id)
        if not exists: 
            await interaction.response.send_message("User does not exist in the database", ephemeral=True)
            return

        result = await databaseManager.getUserInfo(user.id)
        username, tier, lastTest, gamemode, restricted, uuid = result

        await interaction.response.send_message(
            embed=nextcord.Embed.from_dict(
                format.formatinfo(
                    discordName=str(user.name),
                    username=username, 
                    tier=tier, 
                    lastTest=lastTest, 
                    gamemode=gamemode, 
                    restricted=restricted, 
                    uuid=uuid
                )
            )
        )
    except Exception as e: 
        logging.exception("Error in /info command:")
        await interaction.response.send_message(content=messages["error"], ephemeral=True)

@bot.slash_command(name="add", description="adds a user to the ticket")
async def add(
    interaction: nextcord.Interaction,
    user: nextcord.User = nextcord.SlashOption(
        description="Enter their discord account",
        required=True,
    )
    ):
    try:
        # Check if user has ANY tester role
        has_tester_role = False
        for gm_data in listGamemodes.values():
            tester_role = gm_data.get("tester_role")
            if tester_role and tester_role in [role.id for role in interaction.user.roles]:
                has_tester_role = True
                break
        
        if not has_tester_role: 
            await interaction.response.send_message(content=messages["noPermission"], ephemeral=True)
            return
        
        if interaction.channel.category.id not in listGamemodeCategories: 
            await interaction.response.send_message(messages["notTicketCatagory"], ephemeral=True)
            return

        channel = interaction.channel
        overwrite = nextcord.PermissionOverwrite()
        overwrite.view_channel = True
        overwrite.send_messages = True
        await channel.set_permissions(user, overwrite=overwrite)
        await interaction.response.send_message(content=f"<@{user.id}> has been added to the ticket!")

    except Exception as e: 
        logging.exception("Error in /add command:")
        await interaction.response.send_message(content=messages["error"], ephemeral=True)

@bot.slash_command(name="remove", description="removes a user from a ticket")
async def remove(
    interaction: nextcord.Interaction,
    user: nextcord.User = nextcord.SlashOption(
        description="Enter their discord account",
        required=True,
    )
    ):
    try:
        # Check if user has ANY tester role
        has_tester_role = False
        for gm_data in listGamemodes.values():
            tester_role = gm_data.get("tester_role")
            if tester_role and tester_role in [role.id for role in interaction.user.roles]:
                has_tester_role = True
                break
        
        if not has_tester_role: 
            await interaction.response.send_message(content=messages["noPermission"], ephemeral=True)
            return
        
        if interaction.channel.category.id not in listGamemodeCategories: 
            await interaction.response.send_message(messages["notTicketCatagory"], ephemeral=True)
            return
        
        channel = interaction.channel
        overwrite = nextcord.PermissionOverwrite()
        overwrite.view_channel = False
        overwrite.send_messages = False
        await channel.set_permissions(user, overwrite=overwrite)
        await interaction.response.send_message(content=f"<@{user.id}> has been removed from the ticket!")

    except Exception as e: 
        logging.exception("Error in /remove command:")
        await interaction.response.send_message(content=messages["error"], ephemeral=True)

@bot.slash_command(name="passeval", description="passes eval")
async def passeval(
    interaction: nextcord.Interaction,
    user: nextcord.User = nextcord.SlashOption(
    description="Enter their discord account",
    required=True,
    )
    ):
    try:
        # Check if user has ANY tester role
        has_tester_role = False
        for gm_data in listGamemodes.values():
            tester_role = gm_data.get("tester_role")
            if tester_role and tester_role in [role.id for role in interaction.user.roles]:
                has_tester_role = True
                break
        
        if not has_tester_role: 
            await interaction.response.send_message(content=messages["noPermission"], ephemeral=True)
            return
        
        if interaction.channel.category.id not in listGamemodeCategories or interaction.channel.id in listGamemodeQueueChannel: 
            await interaction.response.send_message(content="You cannot use this command in this channel", ephemeral=True)
            return
        
        channel = interaction.channel
        await channel.edit(name=f"passeval-{user.name}")
        await interaction.response.send_message(content=f"<@{user.id}> has passed eval!")

    except Exception as e: 
        logging.exception("Error in /passeval command:")
        await interaction.response.send_message(content=messages["error"], ephemeral=True)

if __name__ == "__main__":
    # Start keep_alive server if available (for hosting platforms like Katabump, Replit, etc.)
    if HOSTING_ENABLED:
        start()
        logging.info("Keep-alive server started for hosting platform")
    
    bot.run(os.getenv("TOKEN"))
