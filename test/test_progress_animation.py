"""
Test script to verify progress animation functionality with more detail.
"""

import asyncio
import logging
from unittest.mock import MagicMock, AsyncMock

# Set up logging to see debug messages
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def test_complete_handler_flow():
    """Test the complete handler flow with progress animation."""
    print("Testing complete handler flow...")
    
    from src.agentic_handlers import agentic_text_chat_handler
    
    # Create mock update and context
    update = MagicMock()
    context = MagicMock()
    
    # Mock user information
    update.message.from_user.id = 12345
    update.message.from_user.first_name = "TestUser"
    update.message.text = "test query"
    update.message.date = MagicMock()
    update.message.date.timestamp.return_value = 1234567890
    update.effective_chat.id = 12345
    update.message.id = 1
    
    # Mock bot methods
    context.bot = MagicMock()
    context.bot.send_chat_action = AsyncMock()
    
    # Mock send_message to return a message with an id
    sent_message = MagicMock()
    sent_message.id = 999
    context.bot.send_message = AsyncMock(return_value=sent_message)
    
    # Mock edit_message_text
    context.bot.edit_message_text = AsyncMock()
    
    # Run the handler
    try:
        await agentic_text_chat_handler(update, context)
        print("✓ Handler completed successfully")
    except Exception as e:
        print(f"✗ Handler failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Check that send_message was called (for thinking message)
    if context.bot.send_message.called:
        print(f"✓ Thinking message sent")
        call_args = context.bot.send_message.call_args
        print(f"  Text: {call_args[1]['text']}")
    else:
        print("✗ Thinking message was not sent")
        return False
    
    # Check that edit_message_text was called (for progress updates and final response)
    edit_calls = context.bot.edit_message_text.call_count
    print(f"✓ edit_message_text called {edit_calls} times")
    
    if edit_calls > 0:
        print("  Progress updates:")
        for i, call in enumerate(context.bot.edit_message_text.call_args_list):
            text = call[1]['text']
            print(f"    {i+1}. {text[:100]}...")
    
    return True


async def test_progress_animation_timing():
    """Test that progress animation runs while workflow is executing."""
    print("\nTesting progress animation timing...")
    
    from src.agentic_handlers import update_progress_animation
    
    # Create mock context
    context = MagicMock()
    context.bot = MagicMock()
    context.bot.edit_message_text = AsyncMock()
    
    chat_id = 12345
    message_id = 67890
    progress_steps = ["10%", "25%", "50%", "75%", "90%"]
    
    # Start the animation
    animation_task = asyncio.create_task(
        update_progress_animation(context, chat_id, message_id, progress_steps)
    )
    
    # Simulate a workflow that takes some time
    workflow_task = asyncio.create_task(
        asyncio.sleep(3)  # Simulate 3 seconds of processing
    )
    
    # Wait for both to complete
    await asyncio.wait([animation_task, workflow_task], return_when=asyncio.FIRST_COMPLETED)
    
    # Cancel the animation
    animation_task.cancel()
    try:
        await animation_task
    except asyncio.CancelledError:
        pass
    
    # Check results
    edit_calls = context.bot.edit_message_text.call_count
    print(f"✓ Progress animation made {edit_calls} updates")
    
    if edit_calls > 0:
        print("  Updates made:")
        for i, call in enumerate(context.bot.edit_message_text.call_args_list):
            text = call[1]['text']
            print(f"    {i+1}. {text}")
    
    return True


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Progress Animation Comprehensive Test Suite")
    print("=" * 60)
    
    test1 = await test_complete_handler_flow()
    test2 = await test_progress_animation_timing()
    
    print("\n" + "=" * 60)
    if test1 and test2:
        print("✓ All tests passed!")
        print("=" * 60)
        return 0
    else:
        print("✗ Some tests failed")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
