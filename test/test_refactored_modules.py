"""
Test to verify the refactored modules work correctly
"""
import asyncio
import logging
from src.mongo import MongoDBManager
from src.history import MongoDBChatMessageHistory
from src.ollama import OllamaClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_mongodb_manager():
    """Test MongoDBManager initialization and methods."""
    print("Testing MongoDBManager...")
    
    # Create manager
    manager = MongoDBManager(host="localhost", port=27017, default_db="test_db")
    
    # Test initialization
    try:
        await manager.initialize()
        print("✓ MongoDBManager initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        return False
    
    # Test get_database
    try:
        db = manager.get_database()
        print("✓ get_database() works with default db")
        
        db2 = manager.get_database("another_db")
        print("✓ get_database() works with custom db")
    except Exception as e:
        print(f"✗ Failed to get database: {e}")
        return False
    
    # Test ping
    try:
        result = await manager.ping()
        print(f"✓ Ping result: {result}")
    except Exception as e:
        print(f"✗ Ping failed: {e}")
        return False
    
    # Test error handling
    try:
        uninitialized_manager = MongoDBManager(host="localhost", port=27017)
        uninitialized_manager.get_database()
        print("✗ Should have raised RuntimeError for uninitialized manager")
        return False
    except RuntimeError:
        print("✓ Correctly raises RuntimeError for uninitialized manager")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False
    
    manager.close()
    print("✓ MongoDBManager tests passed\n")
    return True


async def test_history_manager():
    """Test MongoDBChatMessageHistory with MongoDBManager."""
    print("Testing MongoDBChatMessageHistory...")
    
    # Create and initialize manager
    manager = MongoDBManager(host="localhost", port=27017, default_db="test_db")
    await manager.initialize()
    
    try:
        # Create history instance
        history = MongoDBChatMessageHistory(
            collection_name="test_collection",
            session_id="test_session_123",
            mongodb_manager=manager
        )
        print("✓ MongoDBChatMessageHistory initialized successfully")
        
        # Test clear (should work even if empty)
        await history.clear()
        print("✓ clear() works")
        
        # Test messages property
        messages = await history.messages
        print(f"✓ messages property works, returned {len(messages)} messages")
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    finally:
        manager.close()
    
    print("✓ MongoDBChatMessageHistory tests passed\n")
    return True


async def test_ollama_client():
    """Test OllamaClient initialization."""
    print("Testing OllamaClient...")
    
    try:
        # Create client (won't actually connect, just test initialization)
        client = OllamaClient(host="http://localhost:11434", model="llama2")
        print("✓ OllamaClient initialized successfully")
        print(f"✓ Host: {client.host}")
        print(f"✓ Model: {client.model}")
        print(f"✓ Timeout: {client.timeout}")
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    print("✓ OllamaClient tests passed\n")
    return True


async def test_legacy_functions():
    """Test that legacy functions still work."""
    print("Testing legacy functions...")
    
    try:
        # These should work without errors (though they won't connect)
        from src.ollama import ollama_request, ollama_chat, ollama_chat_stream
        print("✓ Legacy functions can be imported")
        
        # Check function signatures
        import inspect
        sig = inspect.signature(ollama_request)
        params = list(sig.parameters.keys())
        if 'host' in params and 'model' in params:
            print("✓ ollama_request has correct signature")
        else:
            print(f"✗ ollama_request signature incorrect: {params}")
            return False
            
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    print("✓ Legacy functions tests passed\n")
    return True


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Refactored Modules Validation Tests")
    print("=" * 60)
    print()
    
    results = []
    
    # Test MongoDBManager
    results.append(await test_mongodb_manager())
    
    # Test MongoDBChatMessageHistory
    results.append(await test_history_manager())
    
    # Test OllamaClient
    results.append(await test_ollama_client())
    
    # Test legacy functions
    results.append(await test_legacy_functions())
    
    print("=" * 60)
    if all(results):
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        return 0
    else:
        print("✗ SOME TESTS FAILED!")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
