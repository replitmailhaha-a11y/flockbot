# 🎮 Gamemode-Specific Features

## Overview

The Unified TierList Bot now supports **gamemode-specific tiers and tester roles**, giving you complete control over each gamemode's testing system.

## 🏆 Gamemode-Specific Tiers

Each gamemode has its **own tier structure** with separate roles. This means:

- **Mace** has its own LT5-HT1 roles
- **NethPot** has its own LT5-HT1 roles  
- **SMP** has its own LT5-HT1 roles
- (And so on for all 8 gamemodes)

### Benefits:
✅ Players can have different tiers in different gamemodes  
✅ Example: LT3 in Mace but HT5 in Sword  
✅ Clear separation of skills per gamemode  
✅ Results show which gamemode the tier is for  

### Setup:

In `config/config.yml`, each gamemode has its own `tiers` section:

```yaml
gamemodes:
    mace: 
        queue_channel: 123456789
        ticket_catagory: 123456789
        role_ping: 123456789
        queue_role: 123456789
        tester_role: 123456789        # Mace tester role
        tiers:                        # Mace-specific tiers
            lt5: 123456789
            ht5: 123456789
            lt4: 123456789
            ht4: 123456789
            lt3: 123456789
            ht3: 123456789
            lt2: 123456789
            ht2: 123456789
            lt1: 123456789
            ht1: 123456789
    nethpot:
        # Same structure with NethPot-specific roles
        tester_role: 123456789
        tiers:
            lt5: 123456789
            # ... etc
```

### Discord Roles to Create:

For **each gamemode**, create these tier roles:
```
Mace:
- mace-lt5
- mace-ht5
- mace-lt4
- mace-ht4
- mace-lt3
- mace-ht3
- mace-lt2
- mace-ht2
- mace-lt1
- mace-ht1

NethPot:
- nethpot-lt5
- nethpot-ht5
- nethpot-lt4
- ... (and so on)

(Repeat for all 8 gamemodes)
```

**Total tier roles:** 8 gamemodes × 10 tiers = **80 tier roles**

## 👥 Gamemode-Specific Tester Roles

Testers can now be **assigned to specific gamemodes**. A Mace tester can only:
- Open/close Mace queues
- Test Mace players
- Give Mace tier results

They **cannot** manage other gamemodes unless given those roles too.

### Benefits:
✅ Specialized testers per gamemode  
✅ Better quality control  
✅ Clear responsibilities  
✅ Prevents testers from managing gamemodes they don't know  

### Setup:

Create **one tester role per gamemode**:
```
- mace-tester
- nethpot-tester
- smp-tester
- sword-tester
- uhc-tester
- axe-tester
- diamondpot-tester
- vanilla-tester
```

Assign these roles in `config/config.yml`:
```yaml
gamemodes:
    mace: 
        tester_role: 123456789  # mace-tester role ID
    nethpot:
        tester_role: 123456789  # nethpot-tester role ID
    # ... etc
```

### How It Works:

**Command Permissions:**

| Command | Permission Check |
|---------|------------------|
| `/results <user> <tier>` | Checks user's gamemode → Requires tester role for THAT gamemode |
| `/openqueue <gamemode>` | Requires tester role for THAT gamemode |
| `/closequeue <gamemode>` | Requires tester role for THAT gamemode |
| `/next <gamemode>` | Requires tester role for THAT gamemode |
| `/closetest` | Requires ANY tester role |
| `/forceclosetest` | Requires ANY tester role |
| `/info` | No tester role required |
| `/updateusername` | Requires ANY tester role |
| `/updatetier` | Requires ANY tester role |
| `/restrict` | Requires ANY tester role |
| `/unrestrict` | Requires ANY tester role |
| `/add` | Requires ANY tester role |
| `/remove` | Requires ANY tester role |
| `/passeval` | Requires ANY tester role |

### Example Scenarios:

**Scenario 1: Mace-Only Tester**
```
User: John
Roles: mace-tester, verified

What John CAN do:
✅ /openqueue mace
✅ /closequeue mace
✅ /next mace
✅ /results (for mace players)

What John CANNOT do:
❌ /openqueue nethpot
❌ /next sword
❌ /results (for nethpot players)
```

**Scenario 2: Multi-Gamemode Tester**
```
User: Sarah
Roles: mace-tester, sword-tester, verified

What Sarah CAN do:
✅ /openqueue mace
✅ /openqueue sword
✅ /next mace
✅ /next sword
✅ /results (for mace AND sword players)

What Sarah CANNOT do:
❌ /openqueue nethpot
❌ /next uhc
```

**Scenario 3: Admin Tester (All Gamemodes)**
```
User: Admin
Roles: mace-tester, nethpot-tester, smp-tester, sword-tester, 
       uhc-tester, axe-tester, diamondpot-tester, vanilla-tester

What Admin CAN do:
✅ Everything! All gamemodes, all commands
```

## 📊 Results Display

When a tester uses `/results`, the embed now shows:

```
🏆 Tier Test Result

Player: JohnDoe
Tester: @TesterName
Gamemode: MACE                    ← Shows the gamemode!
Minecraft Username: JohnDoe
Previous Tier: LT3
New Tier: HT5                     ← Uses Mace-specific tier roles

[Player gets the mace-ht5 role automatically]
```

The gamemode is displayed in **UPPERCASE** for clarity.

## 🔄 Automatic Role Management

When `/results` is used:

1. **Removes old tier role** from the user's CURRENT gamemode
   - Example: If user is in Mace, removes `mace-lt3`
   
2. **Assigns new tier role** from the gamemode-specific tiers
   - Example: Assigns `mace-ht5`

3. **Does NOT affect other gamemodes**
   - User's Sword tier stays the same
   - User's NethPot tier stays the same

## 📝 Configuration Checklist

Before running the bot:

### 1. Create Discord Roles
- [ ] 8 gamemode player roles (mace-player, nethpot-player, etc.)
- [ ] 8 tester roles (mace-tester, nethpot-tester, etc.)
- [ ] 80 tier roles (10 per gamemode × 8 gamemodes)
- [ ] 1 verified role

### 2. Configure config.yml
- [ ] Fill in all channel IDs
- [ ] Fill in all role IDs
- [ ] Fill in `tester_role` for each gamemode
- [ ] Fill in `tiers` for each gamemode (all 10 tiers)

### 3. Assign Tester Roles
- [ ] Give testers their appropriate gamemode tester roles
- [ ] Example: Give `mace-tester` role to Mace testers

### 4. Test the System
- [ ] Test `/openqueue mace` with mace-tester role
- [ ] Test `/results` - verify correct gamemode shows
- [ ] Test `/results` - verify correct tier role assigned
- [ ] Try using wrong gamemode tester role - should fail

## 💡 Tips

1. **Naming Convention:** Use consistent role names like `gamemode-tier` (e.g., `mace-lt5`)

2. **Tester Hierarchy:**
   - New testers → Start with 1 gamemode
   - Experienced testers → Add more gamemodes
   - Admins → All gamemodes

3. **Role Colors:** Use different colors for each gamemode's tiers for easy visual identification

4. **Category Organization:** Put tier roles in Discord categories by gamemode:
   ```
   📁 Mace Tiers
     - mace-lt5
     - mace-ht5
     - ...
   📁 NethPot Tiers
     - nethpot-lt5
     - ...
   ```

5. **Backup Plan:** Keep the global `tiers` section in config as a fallback (though it won't be used if gamemode tiers are set)

## 🎯 Summary

**What Changed:**
- ✅ Each gamemode has its own tier structure
- ✅ Each gamemode has its own tester role
- ✅ Results show the gamemode clearly
- ✅ Testers can only manage their assigned gamemodes
- ✅ Players can have different tiers per gamemode
- ✅ Automatic role management per gamemode

**What Stayed the Same:**
- ✅ Verification system
- ✅ Queue management
- ✅ Ticket system
- ✅ All commands work the same way
- ✅ Database structure (gamemode already tracked)

Your bot is now fully gamemode-aware with complete separation between gamemodes! 🎮✨
