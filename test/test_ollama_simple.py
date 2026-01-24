
import asyncio
import logging
from src.ollama import OllamaClient
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ollama():
    client = OllamaClient(host=config.OLLAMA_HOST, model=config.OLLAMA_MODEL)
    print(f"Testing Ollama at {config.OLLAMA_HOST} with model {config.OLLAMA_MODEL}...")
    
    try:
        response = await client.request("Say 'Hello' only.")
        print(f"Response: '{response}'")
    except Exception as e:
        print(f"Ollama test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_ollama())
