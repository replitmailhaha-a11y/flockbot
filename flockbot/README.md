# 🎮 Unified TierList Bot

A comprehensive Discord bot that manages tier testing for **8 different Minecraft PvP gamemodes** in a single bot instance with verification system and role-based channel access.

## ✨ Features

- **🎯 Single Bot for All Gamemodes**: Mace, NethPot, SMP, Sword, UHC, Axe, DiamondPot, Vanilla
- **🔐 Verification System**: Users must verify with Minecraft username before accessing queues
- **📋 Dropdown Menu**: Clean UI for gamemode selection
- **👁️ Channel Isolation**: Users only see channels for their selected gamemode
- **🎫 Ticket System**: Automatic ticket creation for testing
- **📊 Queue Management**: Real-time queue updates with tester support
- **🏆 Gamemode-Specific Tiers**: Each gamemode has its own tier structure and roles
- **👥 Gamemode-Specific Testers**: Testers can only manage their assigned gamemodes
- **💾 Database Support**: SQLite (default) or MySQL

## 📋 Prerequisites

- Python 3.8 or higher
- Discord Bot Token
- Discord Server with proper channels and roles set up

## 🚀 Setup Guide

### 1. Installation

```bash
# Navigate to the bot directory
cd UnifiedTierBot

# Install dependencies
pip install -r requirements.txt
```

### 2. Discord Setup

#### Create Channels:
1. **Welcome Channel** - Where users select their gamemode
2. **Queue Channels** (8 total) - One for each gamemode:
   - `#mace-queue`
   - `#nethpot-queue`
   - `#smp-queue`
   - `#sword-queue`
   - `#uhc-queue`
   - `#axe-queue`
   - `#diamondpot-queue`
   - `#vanilla-queue`
3. **Ticket Categories** (8 total) - One for each gamemode's tickets
4. **Results Channel** - Where test results are posted
5. **Verification Log Channel** - Logs verification events

#### Create Roles:
1. **Verified** - Base role for verified users
2. **Gamemode Roles** (8 total) - One for each gamemode:
   - `mace-player`
   - `nethpot-player`
   - `smp-player`
   - `sword-player`
   - `uhc-player`
   - `axe-player`
   - `diamondpot-player`
   - `vanilla-player`
3. **Tester Roles** (8 total) - One for each gamemode:
   - `mace-tester`
   - `nethpot-tester`
   - `smp-tester`
   - `sword-tester`
   - `uhc-tester`
   - `axe-tester`
   - `diamondpot-tester`
   - `vanilla-tester`
4. **Tier Roles** - For each tier PER GAMEMODE (80 roles total):
   - Mace: `mace-lt5`, `mace-ht5`, `mace-lt4`, etc.
   - NethPot: `nethpot-lt5`, `nethpot-ht5`, etc.
   - (Repeat for all 8 gamemodes)

#### Channel Permissions:
- Set queue channels to **deny @everyone** from viewing
- Bot will automatically grant access based on gamemode role

### 3. Configuration

#### a. Create `.env` file:
```bash
# Copy the example
copy .env.example .env

# Edit .env and add your bot token
TOKEN=your_actual_bot_token_here
```

#### b. Edit `config/config.yml`:

Replace all `0` values with actual Discord IDs:

```yaml
bot:
    channels:
        results: 1234567890123456789      # Results channel ID
        welcome: 1234567890123456789      # Welcome channel ID
        verification: 1234567890123456789 # Verification log channel ID

    roles:
        tester: 1234567890123456789       # Tester role ID
        verified: 1234567890123456789     # Verified role ID

    tiers:                                # Tier role IDs
        lt5: 1234567890123456789
        ht5: 1234567890123456789
        # ... add all tier roles

    gamemodes:
        mace: 
            queue_channel: 1234567890123456789   # Queue channel ID
            ticket_catagory: 1234567890123456789 # Ticket category ID
            role_ping: 1234567890123456789       # Role to ping when queue opens
            queue_role: 1234567890123456789      # Role that can see this channel
        # ... configure all 8 gamemodes
```

**How to get Discord IDs:**
1. Enable Developer Mode in Discord (Settings > Advanced > Developer Mode)
2. Right-click on channel/role and select "Copy ID"

### 4. Run the Bot

```bash
python main.py
```

The bot will:
1. Create the database automatically
2. Setup channel permissions
3. Post the gamemode selection message in the welcome channel
4. Be ready to accept verifications!

## 🎯 How It Works

### User Flow:
1. **User joins server** → Sees welcome channel with dropdown
2. **Selects gamemode** → Dropdown appears with 8 gamemodes
3. **Enters details** → Modal asks for:
   - Minecraft Username
   - Region (EU/NA)
   - Preferred Server
4. **Gets verified** → Bot validates username via Mojang API
5. **Receives access** → Bot assigns roles and grants channel access
6. **Joins queue** → User can now see and access their queue channel
7. **Gets tested** → Tester picks them from queue and creates ticket
8. **Receives tier** → Results posted in results channel

### Tester Commands:
- `/openqueue <gamemode>` - Open queue for a gamemode
- `/closequeue <gamemode>` - Close queue
- `/next <gamemode>` - Get next user from queue (creates ticket)
- `/results <user> <tier>` - Close ticket and assign tier
- `/closetest` - Close current ticket
- `/info <user>` - Get user information
- `/restrict <user>` - Restrict user from testing
- `/unrestrict <user>` - Unrestrict user
- `/updateusername <user> <username>` - Update MC username
- `/updatetier <user> <tier>` - Update tier in database

## 📁 Project Structure

```
UnifiedTierBot/
├── config/
│   ├── config.yml              # Main configuration
│   └── *.json                  # Message templates
├── src/
│   ├── database/
│   │   ├── databaseManager.py  # Database interface
│   │   ├── sqlite.py           # SQLite implementation
│   │   └── mysql.py            # MySQL implementation
│   ├── ui/
│   │   ├── gamemodeSelect.py   # Gamemode dropdown
│   │   ├── verificationModal.py # Verification form
│   │   ├── enterQueueButton.py # Queue buttons
│   │   └── closeTicketButton.py # Ticket close button
│   ├── utils/
│   │   ├── loadConfig.py       # Config loader
│   │   ├── format.py           # Message formatter
│   │   ├── mojang.py           # Mojang API
│   │   └── permissions.py      # Channel permissions
│   └── tierlistQueue.py        # Queue management
├── storage/
│   └── database.db             # SQLite database (auto-created)
├── logs/                       # Log files (auto-created)
├── main.py                     # Bot entry point
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
├── .env.example                # Example env file
└── README.md                   # This file
```

## 🔧 Customization

### Modify Messages:
Edit JSON files in `config/` directory:
- `enterwaitlist.json` - Welcome message
- `queue.json` - Queue display message
- `ticket.json` - Ticket message
- `resultmessage.json` - Results message
- `info.json` - User info display
- `noqueue.json` - No queue active message
- `highticket.json` - High tier ticket message

### Add More Gamemodes:
1. Add to `config/config.yml` under `gamemodes:`
2. Update `src/ui/gamemodeSelect.py` with new option
3. Create corresponding channels and roles in Discord

## 🐛 Troubleshooting

**Bot doesn't start:**
- Check if token is correct in `.env`
- Ensure all channel/role IDs in config.yml are valid
- Check console for error messages

**Users can't see queue channels:**
- Verify `queue_role` is set correctly in config
- Check that bot has "Manage Channels" and "Manage Roles" permissions
- Ensure roles are assigned properly

**Queue doesn't update:**
- Check `reloadQueue` setting in config (default: 30 seconds)
- Verify bot has permission to edit messages in queue channels

**Database errors:**
- Delete `storage/database.db` and restart bot to recreate
- Check file permissions on storage folder

## 📝 Notes

- Bot requires a restart after updating config
- Channel permissions are reset on bot startup
- All data is stored in SQLite by default
- Switch to MySQL by changing `database.type` in config.yml

## 🤝 Migration from Old Bots

If migrating from the separate bot setup:

1. **Backup databases** from all 8 bots
2. **Create unified config** with all channel/role IDs
3. **Run new bot** - it will create fresh database
4. **Manually transfer data** if needed (script required)
5. **Decommission old bots** after verification

## 📜 License

This project is licensed under the same license as the original tier testing bots.

## 💡 Support

For issues or questions:
1. Check the troubleshooting section
2. Review console logs in `logs/` folder
3. Verify all configuration is correct

---

**Enjoy your unified tier testing experience! 🎮✨**
