---
name: mongo_manager
description: Manage the persistent chat history and user sessions in MongoDB.
---

# MongoDB Manager Skill

This skill provides instructions for inspecting and managing the chat history stored in MongoDB.

## Instructions

### Exporting Chat History
Use the `scripts/export_history.py` script to dump chat logs for a specific user or all users.

```bash
python3 .agent/skills/mongo_manager/scripts/export_history.py <user_id>
```

### Inspecting MongoDB
You can use the `mongosh` CLI if installed on the system to manually query the database.
Default connection: `mongodb://localhost:27017`
Default DB: `telegram_bot` (or as configured in `config/config.py`)

## troubleshooting
- **Connection Refused**: Ensure MongoDB service is running (`brew services start mongodb-community`).
- **Missing Data**: Check `COLLECTION_NAME` in `.env`.
