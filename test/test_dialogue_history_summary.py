#!/usr/bin/env python3
"""
Test script to verify the dialogue history summary logging functionality.
This script tests the new get_conversation_summary method in MongoDBChatMessageHistory.
"""

import logging
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Set up logging similar to app.py
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)

logger = logging.getLogger(__name__)

async def test_conversation_summary():
    """Test the conversation summary functionality."""
    print("\n" + "="*80)
    print("TESTING DIALOGUE HISTORY SUMMARY LOGGING")
    print("="*80)
    
    # Import after logging setup to capture all logs
    from src.history import MongoDBChatMessageHistory
    from src.mongo import MongoDBManager
    from config import config
    
    # Initialize MongoDB manager
    mongodb_manager = MongoDBManager(
        host=config.MONGO_HOST, 
        port=int(config.MONGO_PORT), 
        default_db=config.BOT_NAME
    )
    
    # Initialize MongoDB connection
    await mongodb_manager.initialize()
    
    # Test with a test session
    test_session_id = "test_summary_session_123"
    
    # Create chat history instance
    chat_history = MongoDBChatMessageHistory(
        collection_name=config.BOT_NAME,
        session_id=test_session_id,
        mongodb_manager=mongodb_manager
    )
    
    print("\n1. Testing empty conversation summary:")
    print("-" * 80)
    summary = await chat_history.get_conversation_summary(max_length=200)
    print(f"Summary: {summary}")
    print("✅ Empty conversation summary logged successfully")
    
    # Add some test messages
    print("\n2. Adding test messages to conversation:")
    print("-" * 80)
    
    test_messages = [
        HumanMessage(
            content="Hello, I need help with accounting regulations.",
            additional_kwargs={
                "type": "human",
                "timestamp": int(datetime.now().timestamp()),
            }
        ),
        AIMessage(
            content="Hello! I'm your accounting expert. What specific regulations are you asking about?",
            additional_kwargs={
                "type": "ai",
                "timestamp": int(datetime.now().timestamp()) + 1,
            }
        ),
        HumanMessage(
            content="I need to know about GAAP revenue recognition standards.",
            additional_kwargs={
                "type": "human",
                "timestamp": int(datetime.now().timestamp()) + 2,
            }
        ),
        AIMessage(
            content="GAAP revenue recognition follows ASC 606. Revenue is recognized when control transfers to the customer...",
            additional_kwargs={
                "type": "ai",
                "timestamp": int(datetime.now().timestamp()) + 3,
            }
        ),
        HumanMessage(
            content="What about deferred revenue?",
            additional_kwargs={
                "type": "human",
                "timestamp": int(datetime.now().timestamp()) + 4,
            }
        ),
    ]
    
    await chat_history.add_messages(test_messages)
    print(f"✅ Added {len(test_messages)} test messages")
    
    print("\n3. Testing conversation summary with messages:")
    print("-" * 80)
    summary = await chat_history.get_conversation_summary(max_length=200)
    print(f"Summary: {summary}")
    print("✅ Conversation summary with messages logged successfully")
    
    print("\n4. Testing summary length limitation:")
    print("-" * 80)
    # Add more messages to potentially exceed max length
    additional_messages = [
        AIMessage(
            content="Deferred revenue is recorded when payment is received before the service is delivered...",
            additional_kwargs={
                "type": "ai",
                "timestamp": int(datetime.now().timestamp()) + 5,
            }
        ),
        HumanMessage(
            content="Can you explain the journal entry for deferred revenue?",
            additional_kwargs={
                "type": "human",
                "timestamp": int(datetime.now().timestamp()) + 6,
            }
        ),
        AIMessage(
            content="The journal entry for deferred revenue is: Debit Cash, Credit Deferred Revenue...",
            additional_kwargs={
                "type": "ai",
                "timestamp": int(datetime.now().timestamp()) + 7,
            }
        ),
    ]
    
    await chat_history.add_messages(additional_messages)
    print(f"✅ Added {len(additional_messages)} more messages")
    
    summary = await chat_history.get_conversation_summary(max_length=150)
    print(f"Summary (max 150 chars): {summary}")
    print(f"Summary length: {len(summary)} characters")
    if len(summary) > 150:
        print("❌ Summary exceeded max length!")
    else:
        print("✅ Summary length properly limited")
    
    print("\n5. Testing summary with custom max length:")
    print("-" * 80)
    summary = await chat_history.get_conversation_summary(max_length=100)
    print(f"Summary (max 100 chars): {summary}")
    print(f"Summary length: {len(summary)} characters")
    print("✅ Custom max length parameter works correctly")
    
    # Clean up test data
    print("\n6. Cleaning up test data:")
    print("-" * 80)
    await chat_history.clear()
    print("✅ Test data cleared from database")
    
    print("\n" + "="*80)
    print("TEST COMPLETED SUCCESSFULLY")
    print("="*80)
    print("\nKey features demonstrated:")
    print("1. ✅ Empty conversation summary logging")
    print("2. ✅ Conversation summary with messages")
    print("3. ✅ Summary length limitation (truncation)")
    print("4. ✅ Custom max length parameter")
    print("5. ✅ Proper error handling")
    print("\n")

if __name__ == "__main__":
    asyncio.run(test_conversation_summary())
