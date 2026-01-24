import json
import logging
from abc import ABC
from typing import List, Optional, Sequence

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, message_to_dict, messages_from_dict
from pymongo import errors
from src.mongo import MongoDBManager

logger = logging.getLogger(__name__)


class MongoDBChatMessageHistory(BaseChatMessageHistory, ABC):
    """Chat message history that stores history in MongoDB."""

    def __init__(
        self,
        collection_name: str,
        session_id: str,
        mongodb_manager: MongoDBManager,
        database_name: Optional[str] = None,
    ):
        """
        Initialize MongoDB chat message history.
        
        Args:
            collection_name: Name of the collection to use
            session_id: Unique identifier for the chat session
            mongodb_manager: MongoDB manager instance
            database_name: Optional database name. Uses manager's default if None.
            
        Raises:
            RuntimeError: If MongoDB connection is not initialized
        """
        self.collection_name = collection_name
        self.session_id = session_id
        self.mongodb_manager = mongodb_manager
        self.database_name = database_name

        try:
            db = mongodb_manager.get_database(database_name)
            self.collection = db[collection_name]
            self.collection.create_index("session_id")
            logger.debug(f"Initialized MongoDBChatMessageHistory for session {session_id}")
        except errors.ConnectionFailure as error:
            logger.error(f"Could not connect to MongoDB: {error}")
            raise
        except RuntimeError as error:
            logger.error(f"MongoDB connection not initialized: {error}")
            raise

    @property
    async def messages(self) -> List[BaseMessage]:  # type: ignore
        """Retrieve the messages from MongoDB.
        
        Returns:
            List of BaseMessage objects
            
        Raises:
            errors.OperationFailure: If query fails
        """
        try:
            cursor = self.collection.find({"session_id": self.session_id}).sort("_id", 1)
        except errors.OperationFailure as error:
            logger.error(f"Could not find documents in MongoDB: {error}")
            raise

        if cursor:
            items = [json.loads(document["history"]) async for document in cursor]
        else:
            items = []

        messages = messages_from_dict(items)
        return messages

    async def add_message(self, message: BaseMessage) -> None:
        """Append the message to the record in MongoDB.
        
        Args:
            message: Message to add
            
        Raises:
            errors.WriteError: If write fails
        """
        try:
            await self.collection.insert_one(
                {
                    "session_id": self.session_id,
                    "history": json.dumps(message_to_dict(message)),
                }
            )
            logger.debug(f"Added message to session {self.session_id}")
        except errors.WriteError as err:
            logger.error(f"Could not write document to MongoDB: {err}")
            raise

    async def add_messages(self, messages: Sequence[BaseMessage]) -> None:
        """Append the messages to the record in MongoDB.
        
        Args:
            messages: Sequence of messages to add
            
        Raises:
            errors.BulkWriteError: If write fails
        """
        try:
            await self.collection.insert_many(
                [
                    {
                        "session_id": self.session_id,
                        "history": json.dumps(message_to_dict(message)),
                    }
                    for message in messages
                ]
            )
            logger.debug(f"Added {len(messages)} messages to session {self.session_id}")
        except errors.BulkWriteError as err:
            logger.error(f"Could not write documents to MongoDB: {err}")
            raise

    async def clear(self) -> None:
        """Clear session memory from MongoDB.
        
        Raises:
            errors.WriteError: If delete fails
        """
        try:
            result = await self.collection.delete_many({"session_id": self.session_id})
            logger.debug(f"Cleared {result.deleted_count} documents for session {self.session_id}")
        except errors.WriteError as err:
            logger.error(f"Could not delete documents from MongoDB: {err}")
            raise

    async def get_conversation_summary(self, max_length: int = 500) -> str:
        """Generate a concise summary of the conversation history for logging.
        
        Args:
            max_length: Maximum length of the summary in characters
            
        Returns:
            A concise summary of the conversation
            
        Raises:
            errors.OperationFailure: If query fails
        """
        try:
            messages = await self.messages
            logger.info(f"Looking up chat history for session {self.session_id}...")
        except errors.OperationFailure as error:
            logger.error(f"Could not retrieve messages for summary: {error}")
            raise
        
        if not messages:
            summary = "No conversation history available"
            logger.info(f"Chat History for {self.session_id}: {summary}")
            return summary
        
        # Extract message content and create concise summary
        message_texts = []
        for msg in messages:
            content = msg.content
            # Use msg.type directly if available (LangChain messages have this)
            m_type = getattr(msg, 'type', 'unknown')
            
            if m_type == 'human':
                message_texts.append(f"User: {content[:100]}")
            elif m_type == 'ai':
                message_texts.append(f"AI: {content[:100]}")
            elif m_type == 'system':
                message_texts.append(f"System: {content[:50]}")
            else:
                message_texts.append(f"{m_type.capitalize()}: {content[:50]}")
        
        # Create summary from last 5 messages (most recent context)
        count = len(messages)
        summary = f"Conversation History ({count} messages): "
        summary += " | ".join(message_texts[-5:])  # Last 5 messages with separator
        
        if len(summary) > max_length:
            # Ensure we don't exceed max_length including the ellipsis
            summary = summary[:max_length - 3] + "..."
        
        logger.info(f"Chat History Summary for {self.session_id}: {summary}")
        return summary
