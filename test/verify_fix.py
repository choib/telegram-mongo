
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from src.llm_factory import get_llm_client
from src.llm.ollama import OllamaClient

def test_instantiation():
    try:
        client = get_llm_client()
        print(f"Successfully instantiated client: {type(client)}")
        if isinstance(client, OllamaClient):
            print(f"Ollama host: {client.host}")
            print(f"Ollama model: {client.model}")
        return True
    except TypeError as e:
        print(f"TypeError during instantiation: {e}")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

if __name__ == "__main__":
    if test_instantiation():
        sys.exit(0)
    else:
        sys.exit(1)
