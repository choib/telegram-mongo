---
name: telegram_bot_manager
description: Streamline testing and management of the Telegram bot interface.
---

# Telegram Bot Manager Skill

This skill helps in testing the Telegram bot connectivity and handling common deployment issues.

## Instructions

### Checking Bot Health
Use the `scripts/check_bot_health.py` script to verify if the bot token is valid and if the bot can connect to the Telegram API.

```bash
python3 .agent/skills/telegram_bot_manager/scripts/check_bot_health.py
```

### Resetting Webhooks
If the bot is not receiving messages, you might need to reset the webhook (though this bot currently uses polling).

## Common Issues
- **Conflict Error**: occurs if multiple instances of the bot are running. Use `ps aux | grep app.py` to find and kill processes.
- **Network Error**: Check your internet connection and ensure `api.telegram.org` is reachable.
