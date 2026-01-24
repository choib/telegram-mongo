
import os
import asyncio
import sys
from telegram import Bot
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.getcwd())

async def check_health():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN not found in environment.")
        return False
    
    print(f"Verifying token: {token[:10]}...{token[-5:]}")
    
    bot = Bot(token=token)
    try:
        me = await bot.get_me()
        print(f"Success! Bot connected.")
        print(f"Bot Name: {me.first_name}")
        print(f"Bot Username: @{me.username}")
        return True
    except Exception as e:
        print(f"FAILED to connect to Telegram: {e}")
        return False

if __name__ == "__main__":
    load_dotenv()
    if asyncio.run(check_health()):
        sys.exit(0)
    else:
        sys.exit(1)
