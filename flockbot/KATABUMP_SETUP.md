# Katabump.com Bot Deployment Guide

Dieser Bot ist jetzt vollständig für das Hosting auf **Katabump.com** vorbereitet!

## Schritt-für-Schritt Anleitung

### 1. **GitHub Repository erstellen**
- Gehe zu [github.com](https://github.com)
- Erstelle ein neues Repository
- Lade alle Dateien dieses Bots hoch (oder nutze git):
  ```bash
  git init
  git add .
  git commit -m "Initial commit"
  git remote add origin https://github.com/DEIN-USERNAME/UnifiedTierBot.git
  git branch -M main
  git push -u origin main
  ```

### 2. **Katabump Account erstellen**
- Gehe zu [katabump.com](https://katabump.com)
- Melde dich mit Discord an
- Bestätige die OAuth-Berechtigungen

### 3. **Bot auf Katabump deployen**
1. Klicke auf "New Bot" oder "Deploy"
2. Wähle dein GitHub Repository
3. Wähle den `main` Branch
4. Bestätige die Konfiguration
5. Der Bot wird automatisch deployed!

### 4. **Environment Variablen konfigurieren**
Auf Katabump musst du folgende Umgebungsvariablen setzen:

1. Gehe zu deinem Bot auf Katabump
2. Klicke auf "Settings" → "Environment Variables"
3. Füge folgende Variablen hinzu:

```
TOKEN=DEIN_DISCORD_BOT_TOKEN
DATABASE_TYPE=sqlite  # oder "mysql"
DATABASE_HOST=localhost
DATABASE_USER=root
DATABASE_PASSWORD=dein_passwort
DATABASE_NAME=tierbot
```

### 5. **Discord Bot Token finden**
1. Gehe zu [Discord Developer Portal](https://discord.com/developers/applications)
2. Klicke auf "New Application"
3. Gib deinem Bot einen Namen
4. Kopiere den Token unter "TOKEN" im "Bot" Tab

### 6. **Bot zu Discord Server hinzufügen**
1. Im Developer Portal: Gehe zu "OAuth2" → "URL Generator"
2. Wähle folgende Scopes:
   - `bot`
3. Wähle folgende Permissions:
   - `administrator` (oder spezifische Permissions)
4. Kopiere die generierte URL und öffne sie im Browser
5. Wähle deinen Server aus und autorisiere

### 7. **Bot starten**
- Auf Katabump sollte der Bot automatisch starten
- Checke die "Logs" im Dashboard, um Fehler zu sehen

## Features

✅ **Keep-Alive Server** - Der Bot bleibt 24/7 online (Procfile & keep_alive.py)
✅ **Automatic Deployments** - Updates von GitHub werden automatisch deployt
✅ **Database Support** - SQLite und MySQL Unterstützung
✅ **Logging** - Alle Aktivitäten werden geloggt

## Troubleshooting

### Bot startet nicht
- Überprüfe die **Logs** im Katabump Dashboard
- Stelle sicher, dass der Discord **TOKEN** richtig gesetzt ist
- Überprüfe ob alle Dependencies in `requirements.txt` sind

### Database Fehler
- Stelle sicher, dass `DATABASE_TYPE` korrekt gesetzt ist
- Für MySQL: Kontrolliere Host, User, Passwort und Datenbanknamen

### Logs anschauen
```bash
# Im Katabump Dashboard unter "Logs"
# Oder lokal mit:
tail -f logs/logs-*.log
```

## Zusätzliche Tipps

- **Auto-Restart**: Katabump startet den Bot automatisch neu wenn er crasht
- **Updates**: Pushe einfach auf GitHub und Katabump deployt automatisch
- **Backups**: Nutze MySQL für Datenbanken um Daten zu sichern
- **Monitoring**: Überprüfe regelmäßig die Logs auf Fehler

## Weitere Links

- [Katabump Dokumentation](https://katabump.com/docs)
- [Discord.py Dokumentation](https://docs.discord.py/)
- [Nextcord Dokumentation](https://docs.nextcord.dev/)

---

Bei Fragen oder Problemen, schreib einen Issue auf GitHub! 🚀
