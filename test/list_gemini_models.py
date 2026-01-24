import asyncio
import aiohttp
import os
import sys

# Add the project root to path to import config
sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))
from config import config

async def list_models():
    api_key = config.GEMINI_API_KEY
    if not api_key:
        print("Error: GEMINI_API_KEY not found in config/.env")
        return

    print(f"Checking available models for your API key...")
    
    # Try both v1 and v1beta
    for version in ["v1", "v1beta"]:
        url = f"https://generativelanguage.googleapis.com/{version}/models"
        headers = {"x-goog-api-key": api_key}
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        models = data.get("models", [])
                        print(f"\n--- Available Models ({version}) ---")
                        for m in models:
                            # Print only the name after 'models/'
                            full_name = m.get("name", "")
                            short_name = full_name.split("/")[-1] if "/" in full_name else full_name
                            print(f"- {short_name} (Full: {full_name})")
                    else:
                        print(f"Failed to list models with {version}: {resp.status}")
            except Exception as e:
                print(f"Error checking {version}: {e}")

if __name__ == "__main__":
    asyncio.run(list_models())
