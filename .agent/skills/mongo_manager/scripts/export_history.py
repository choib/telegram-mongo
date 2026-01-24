
import sys
import os
import json

# Add project root to sys.path
sys.path.append(os.getcwd())

from db.mongodb_manager import MongoDBManager
from config import config

def export_history(user_id=None):
    db_manager = MongoDBManager()
    
    if user_id:
        print(f"Exporting history for user: {user_id}")
        messages = db_manager.get_history(user_id)
        filename = f"history_{user_id}.json"
    else:
        print("Exporting all history...")
        # Note: MongoDBManager might need a get_all_history method if not exists
        # For now, let's assume we need a user_id or implement a basic dump
        try:
            users = db_manager.db[config.COLLECTION_NAME].distinct("user_id")
            messages = {}
            for uid in users:
                messages[uid] = db_manager.get_history(uid)
            filename = "all_history.json"
        except Exception as e:
            print(f"Error fetching all history: {e}")
            return

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully exported to {filename}")

if __name__ == "__main__":
    user_id = sys.argv[1] if len(sys.argv) > 1 else None
    export_history(user_id)
