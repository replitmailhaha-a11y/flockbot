import nextcord
from nextcord import ui
import logging

from src.database import databaseManager
from src.utils.mojang import getuserid
from src.utils.loadConfig import messages, listGamemodes, verifiedRole, channels
from src.utils.permissions import grant_gamemode_access

class VerificationModal(ui.Modal):
    def __init__(self, gamemode: str):
        super().__init__(title=f"Verify for {gamemode.title()} Tier Testing")
        self.gamemode = gamemode
        
        self.ign = ui.TextInput(
            label="Minecraft Username", 
            placeholder="Enter your Minecraft username", 
            required=True,
            style=nextcord.TextInputStyle.short
        )
        self.region = ui.TextInput(
            label="Region (EU/NA)", 
            placeholder="Enter your region (EU or NA)", 
            style=nextcord.TextInputStyle.short, 
            required=True
        )
        self.server = ui.TextInput(
            label="Preferred Server", 
            placeholder="Enter the server you play on", 
            style=nextcord.TextInputStyle.short, 
            required=True
        )
        
        self.add_item(self.ign)
        self.add_item(self.region)
        self.add_item(self.server)
    
    async def callback(self, interaction: nextcord.Interaction):
        try:
            # Validate region
            region_value = self.region.value.upper()
            if region_value not in ["EU", "NA"]:
                await interaction.response.send_message(
                    content="❌ Invalid region! Please enter either EU or NA.", 
                    ephemeral=True
                )
                return
            
            # Validate Minecraft username
            uuid = await getuserid(self.ign.value)
            if uuid == "8667ba71b85a4004af54457a9734eed7":
                await interaction.response.send_message(
                    content="❌ Minecraft username does not exist! Please check and try again.", 
                    ephemeral=True
                )
                return
            
            # Check if user already exists and is verified for this gamemode
            exists = await databaseManager.userExists(interaction.user.id)
            if exists:
                is_verified = await databaseManager.isVerified(interaction.user.id, self.gamemode)
                
                if is_verified:
                    await interaction.response.send_message(
                        content="✅ You are already verified for this gamemode!", 
                        ephemeral=True
                    )
                    return
            
            # Add/update user in database
            await databaseManager.addUser(
                discordID=interaction.user.id,
                minecraftUsername=self.ign.value,
                minecraftUUID=uuid,
                tier="none",
                lastTest=0,
                server=self.server.value,
                gamemode=self.gamemode,
                region=region_value,
                verified=True
            )
            
            # Grant access to gamemode channel
            success = await grant_gamemode_access(
                member=interaction.user,
                gamemode=self.gamemode,
                gamemodes=listGamemodes
            )
            
            if not success:
                await interaction.response.send_message(
                    content="❌ Failed to grant channel access. Please contact an admin.", 
                    ephemeral=True
                )
                return
            
            guild = interaction.guild
            
            # Add verified role
            verified_role = guild.get_role(verifiedRole)
            if verified_role:
                await interaction.user.add_roles(verified_role, reason="User verified for tier testing")
            
            # Add gamemode-specific verification role
            gamemode_data = listGamemodes[self.gamemode]
            verification_role_id = gamemode_data.get("verification_role", 0)
            if verification_role_id and verification_role_id != 0:
                verification_role = guild.get_role(verification_role_id)
                if verification_role:
                    await interaction.user.add_roles(verification_role, reason=f"User verified for {self.gamemode} tier testing")
                    logging.info(f"Assigned {self.gamemode} verification role to {interaction.user.name}")
                else:
                    logging.warning(f"Verification role {verification_role_id} for gamemode {self.gamemode} not found")
            
            # Get the queue channel for this gamemode
            queue_channel = guild.get_channel(gamemode_data["queue_channel"])
            channel_mention = f"<#{queue_channel.id}>" if queue_channel else "the queue channel"
            
            # Send success message
            await interaction.response.send_message(
                content=f"✅ **Verification Successful!**\n\n"
                        f"You now have access to {channel_mention}\n"
                        f"Click the 'Enter Queue' button to join the queue!",
                ephemeral=True
            )
            
            # Log verification
            log_channel = guild.get_channel(channels.get("verification", 0))
            if log_channel:
                embed = nextcord.Embed(
                    title="✅ New Verification",
                    description=f"{interaction.user.mention} verified for **{self.gamemode}**",
                    color=nextcord.Color.green()
                )
                embed.add_field(name="Username", value=self.ign.value, inline=True)
                embed.add_field(name="Region", value=region_value, inline=True)
                embed.add_field(name="Server", value=self.server.value, inline=True)
                embed.set_footer(text=f"ID: {interaction.user.id}")
                await log_channel.send(embed=embed)
            
            logging.info(f"User {interaction.user.name} ({interaction.user.id}) verified for {self.gamemode}")
            
        except Exception as e:
            logging.exception(f"Error in verification modal for {self.gamemode}:")
            await interaction.response.send_message(
                content="❌ An error occurred during verification. Please try again or contact an admin.", 
                ephemeral=True
            )
