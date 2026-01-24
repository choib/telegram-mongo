import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from src.agents import get_agent_graph

@pytest.mark.asyncio
async def test_early_clarification_vague_query():
    """Test that a vague query triggers the clarify node and bypasses retrieval."""
    
    # Mock LLM response for augmentation quality to be low
    quality_response = '{"score": 20, "reasoning": "This is a very vague query."}'
    
    # Mock LLM response for supplement questions
    questions_response = '["Could you please clarify what you mean?", "What specific topic are you interested in?"]'
    
    vague_query = "Hey"
    
    with patch("src.ollama.OllamaClient.chat", new_callable=AsyncMock) as mock_chat:
        # First call: Judge Augmentation Quality
        # Second call: Generate Supplement Questions
        mock_chat.side_effect = [quality_response, questions_response]
        
        # We also need to mock the stream for analyze_query and extract_history_context
        # But wait, agents.py uses chat_stream for extraction and augmentation.
        
        with patch("src.ollama.OllamaClient.chat_stream") as mock_stream:
            # Analyze Node: extraction context (empty), then augmentation
            async def mock_stream_gen(prompt):
                if "Analyze the following conversation history" in prompt:
                    yield "No significant context found."
                elif "augment the user's question" in prompt:
                    yield "Hey" # No real augmentation
                elif "clarify or rephrase" in prompt:
                    yield "Hey"
                else:
                    yield ""

            mock_stream.side_effect = mock_stream_gen
            
            graph = await get_agent_graph()
            
            # Run the graph
            result = await graph.ainvoke({
                "query": vague_query,
                "context": ""
            })
            
            # Verify results
            assert result["quality_low"] is True
            assert "final_response" in result
            assert "Could you please clarify" in result["final_response"]
            assert "1. Could you please clarify" in result["final_response"]
            
            # Check if rag_result and web_result are NOT present or are in their initial state
            # Since retrieval node was bypassed, they shouldn't even be in the returned dict if they weren't initialized
            # Actually, TypedDict state usually keeps all keys if they are initialized.
            # In retrieval_node, they are set. If retrieval_node is skipped, they might be missing or None.
            assert "rag_result" not in result or result["rag_result"] is None
            assert "web_result" not in result or result["web_result"] is None
            
            print("Early clarification test passed!")

if __name__ == "__main__":
    asyncio.run(test_early_clarification_vague_query())
