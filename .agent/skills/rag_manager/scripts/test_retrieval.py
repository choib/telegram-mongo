
import sys
import os
import asyncio

# Add project root to sys.path
sys.path.append(os.getcwd())

from rag import RAGManager
from config import config

async def test_retrieval(query):
    print(f"Testing retrieval for query: '{query}'")
    print(f"Database: {config.DATABASE}")
    
    rag = RAGManager()
    
    # Check if database exists
    if not os.path.exists(config.DATABASE):
        print(f"ERROR: Database directory not found at {config.DATABASE}")
        return

    try:
        results = rag.search(query, k=5)
        print(f"\nFound {len(results)} results:")
        for i, res in enumerate(results):
            print(f"\n--- Result {i+1} ---")
            print(f"Source: {res.metadata.get('source', 'unknown')}")
            print(f"Content snippet: {res.page_content[:200]}...")
    except Exception as e:
        print(f"Error during search: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 .agent/skills/rag_manager/scripts/test_retrieval.py <query>")
        sys.exit(1)
    
    query = sys.argv[1]
    asyncio.run(test_retrieval(query))
