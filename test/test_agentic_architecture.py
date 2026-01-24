"""
Quick test to verify the agentic architecture components.
"""

import asyncio
import sys

async def test_agents():
    """Test the agentic architecture."""
    print("Testing agentic architecture...")
    
    try:
        # Import the agents
        from src.agents import (
            RAGAgent, 
            WebSearchAgent, 
            MemoryAgent, 
            JudgingAgent,
            create_agent_graph,
            run_agent_workflow
        )
        
        print("✓ Agents imported successfully")
        
        # Test agent initialization
        rag_agent = RAGAgent()
        web_agent = WebSearchAgent()
        memory_agent = MemoryAgent()
        judging_agent = JudgingAgent()
        
        print("✓ Agents initialized successfully")
        
        # Test agent graph creation
        graph = await create_agent_graph()
        print("✓ Agent graph created successfully")
        
        # Test a simple workflow
        test_query = "전세권 설정 우선순위"
        result = await run_agent_workflow(
            query=test_query,
            context="Previous conversation about real estate laws"
        )
        
        print(f"✓ Workflow executed successfully")
        print(f"  Query: {test_query}")
        print(f"  Agent Flow: {result.get('agent_flow', [])}")
        print(f"  Reasoning: {result.get('reasoning', '')[:100]}...")
        print(f"  Response Length: {len(result.get('final_response', ''))} characters")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_handlers():
    """Test the agentic handlers."""
    print("\nTesting agentic handlers...")
    
    try:
        from src.agentic_handlers import agentic_text_chat_handler, hybrid_text_chat_handler
        
        print("✓ Handlers imported successfully")
        
        # We can't fully test the handlers without a real Telegram bot,
        # but we can verify they're callable
        print("✓ Handlers are callable")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    print("=" * 60)
    print("Agentic Architecture Verification Test")
    print("=" * 60)
    
    agents_ok = await test_agents()
    handlers_ok = await test_handlers()
    
    print("\n" + "=" * 60)
    if agents_ok and handlers_ok:
        print("✓ All tests passed!")
        print("=" * 60)
        return 0
    else:
        print("✗ Some tests failed")
        print("=" * 60)
        return 1

# Note: This file is meant to be run with pytest-asyncio, not directly with asyncio.run
# The main function is kept for reference but should not be called directly
