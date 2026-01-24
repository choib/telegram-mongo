"""
Test script to verify the confidence assessment implementation.
"""
import asyncio
from unittest.mock import MagicMock, AsyncMock


async def test_confidence_assessment():
    """Test the confidence assessment functionality."""
    print("Testing confidence assessment implementation...")
    
    # Import the judging agent
    from src.agents import judging_agent
    
    # Test query and answer
    query = "전세권 설정 우선순위"
    answer = "전세권은 부동산에 대한 우선권을 제공합니다."
    context = "이전 대화에서 부동산 법에 대해 논의했습니다."
    
    # Test confidence assessment
    print("\n1. Testing confidence assessment...")
    confidence = await judging_agent.assess_confidence(query, answer, context)
    print(f"   Confidence score: {confidence.get('confidence_score', 0)}%")
    print(f"   Reasoning: {confidence.get('reasoning', 'None')[:100]}...")
    
    # Test supplement question generation
    print("\n2. Testing supplement question generation...")
    questions = await judging_agent.generate_supplement_questions(
        query, answer, confidence
    )
    print(f"   Number of questions: {len(questions)}")
    for i, q in enumerate(questions, 1):
        print(f"   {i}. {q}")
    
    print("\n✓ Confidence assessment test completed successfully!")


async def test_handler_integration():
    """Test the handler integration."""
    print("\n\nTesting handler integration...")
    
    from src.agentic_handlers import agentic_text_chat_handler
    
    # Create mock update and context
    update = MagicMock()
    context = MagicMock()
    
    update.message.from_user.id = 12345
    update.message.from_user.first_name = "TestUser"
    update.message.text = "간단한 테스트 질문"
    update.message.date = MagicMock()
    update.effective_chat.id = 12345
    update.message.id = 1
    
    # Mock bot methods
    context.bot.send_chat_action = AsyncMock()
    context.bot.send_message = AsyncMock(return_value=MagicMock(id=1))
    context.bot.edit_message_text = AsyncMock()
    
    # Mock the agent workflow to return a simple response
    from src.agents import run_agent_workflow
    run_agent_workflow = AsyncMock(return_value={
        'final_response': '이것은 테스트 답변입니다.',
        'agent_flow': ['RAG'],
        'reasoning': '테스트용'
    })
    
    # Run the handler
    try:
        await agentic_text_chat_handler(update, context)
        print("✓ Handler integration test completed successfully!")
    except Exception as e:
        print(f"✗ Handler test failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests."""
    print("=" * 60)
    print("CONFIDENCE ASSESSMENT IMPLEMENTATION TEST")
    print("=" * 60)
    
    await test_confidence_assessment()
    await test_handler_integration()
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
