import nextcord
import logging

async def setup_gamemode_channel_permissions(guild: nextcord.Guild, gamemodes: dict):
    """Setup channel permissions for all gamemode channels on bot startup"""
    try:
        for gamemode, data in gamemodes.items():
            queue_channel = guild.get_channel(data["queue_channel"])
            if queue_channel is None:
                logging.warning(f"Queue channel for {gamemode} not found: {data['queue_channel']}")
                continue
            
            queue_role = guild.get_role(data["queue_role"])
            if queue_role is None:
                logging.warning(f"Queue role for {gamemode} not found: {data['queue_role']}")
                continue
            
            # Deny @everyone from viewing the channel
            overwrite = nextcord.PermissionOverwrite(view_channel=False)
            await queue_channel.set_permissions(guild.default_role, overwrite=overwrite)
            
            # Allow queue_role to view the channel
            overwrite = nextcord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
            await queue_channel.set_permissions(queue_role, overwrite=overwrite)
            
            logging.info(f"Setup permissions for {gamemode} queue channel")
    except Exception as e:
        logging.exception(f"Error setting up gamemode channel permissions: {e}")

async def grant_gamemode_access(member: nextcord.Member, gamemode: str, gamemodes: dict):
    """Grant a user access to a specific gamemode channel by adding the role"""
    try:
        guild = member.guild
        gamemode_data = gamemodes.get(gamemode)
        if not gamemode_data:
            logging.error(f"Gamemode {gamemode} not found in config")
            return False
        
        queue_role = guild.get_role(gamemode_data["queue_role"])
        if queue_role is None:
            logging.error(f"Queue role for {gamemode} not found: {gamemode_data['queue_role']}")
            return False
        
        # Add the role to the user
        await member.add_roles(queue_role, reason=f"Verified for {gamemode} tier testing")
        logging.info(f"Granted {gamemode} access to {member.name} ({member.id})")
        return True
    except Exception as e:
        logging.exception(f"Error granting gamemode access: {e}")
        return False
