import nextcord
from nextcord import ui

from src.utils.loadConfig import messages, channels
from src.tierlistQueue import TierlistQueue
from src.database import databaseManager

class EnterQueueButton(ui.View):
    def __init__(self, queue):
        super().__init__(timeout=None)
        self.queue: TierlistQueue = queue


    @nextcord.ui.button(label="Enter Queue", style=nextcord.ButtonStyle.primary, custom_id="joinQueue")
    async def enter_queue(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        try:
            # Check if user exists and is verified
            exists = await databaseManager.userExists(interaction.user.id)
            if not exists:
                await interaction.response.send_message(
                    content=messages["notVerified"], 
                    ephemeral=True
                )
                return
            
            is_verified = await databaseManager.isVerified(interaction.user.id)
            if not is_verified:
                await interaction.response.send_message(
                    content=messages["notVerified"], 
                    ephemeral=True
                )
                return
            
            isrestricted = await databaseManager.isRestriced(interaction.user.id)
            if isrestricted: 
                await interaction.response.send_message(
                    content=messages["restricted"], 
                    ephemeral=True
                )
                return
                
            response = await self.queue.addUser(interaction.message.id, interaction.user.id)
            await interaction.response.send_message(content=response, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(content=messages["error"], ephemeral=True)

    @nextcord.ui.button(label="Exit Queue", style=nextcord.ButtonStyle.danger, custom_id="leaveQueue")
    async def exit_queue(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        try:
            response = self.queue.removeUser(interaction.message.id, interaction.user.id)
            await interaction.response.send_message(content=response, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(content=messages["error"], ephemeral=True)
