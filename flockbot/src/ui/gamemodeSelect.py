import nextcord
from nextcord import ui
from src.ui.verificationModal import VerificationModal

class GamemodeSelect(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @ui.select(
        placeholder="Choose your gamemode to get started",
        min_values=1,
        max_values=1,
        options=[
            nextcord.SelectOption(label="mace", description="Mace tier testing", value="mace"),
            nextcord.SelectOption(label="nethpot", description="Netherite Pot tier testing", value="nethpot"),
            nextcord.SelectOption(label="smp", description="SMP tier testing", value="smp"),
            nextcord.SelectOption(label="sword", description="Sword tier testing", value="sword"),
            nextcord.SelectOption(label="uhc", description="UHC tier testing", value="uhc"),
            nextcord.SelectOption(label="axe", description="Axe tier testing", value="axe"),
            nextcord.SelectOption(label="diamondpot", description="Diamond Pot tier testing", value="diamondpot"),
            nextcord.SelectOption(label="vanilla", description="Vanilla tier testing", value="vanilla"),
        ]
    )
    async def select_gamemode(self, select: ui.Select, interaction: nextcord.Interaction):
        try:
            selected_gamemode = select.values[0]
            
            # Check if user is already verified
            from src.database import databaseManager
            exists = await databaseManager.userExists(interaction.user.id)
            
            if exists:
                is_verified = await databaseManager.isVerified(interaction.user.id, selected_gamemode)
                
                if is_verified:
                    await interaction.response.send_message(
                        content="✅ You are already verified for this gamemode! Check the queue channel.",
                        ephemeral=True
                    )
                    return
            
            # Show verification modal
            modal = VerificationModal(gamemode=selected_gamemode)
            await interaction.response.send_modal(modal)
            
        except Exception as e:
            await interaction.response.send_message(
                content="❌ An error occurred. Please try again.",
                ephemeral=True
            )
