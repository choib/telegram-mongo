import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)


class MongoDBManager:
    """Manages MongoDB connections and provides database access."""
    
    def __init__(self, host: str, port: int, default_db: str = "chat_history"):
        """
        Initialize MongoDB manager.
        
        Args:
            host: MongoDB host address
            port: MongoDB port number
            default_db: Default database name
        """
        self.host = host
        self.port = port
        self.default_db = default_db
        self.client: Optional[AsyncIOMotorClient] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the MongoDB connection, ensuring it's valid for the current loop."""
        import asyncio
        
        # Check if we need to recreate the client due to loop closure
        recreate = False
        if self.client is not None:
            try:
                # Motor client doesn't easily expose its loop, but we can try a simple operation
                # If the loop is closed, this might fail or we can check the loop explicitly
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # No loop running, but we are in an async function, so there should be one
                recreate = True
            
        if self.client is None or recreate:
            if self.client:
                self.client.close()
            
            self.client = AsyncIOMotorClient(
                host=self.host,
                port=self.port,
                # Ensure the client is bound to the current loop
                io_loop=asyncio.get_running_loop()
            )
            self._initialized = True
            logger.info(f"Connected to MongoDB at {self.host}:{self.port}")
    
    def get_database(self, db_name: Optional[str] = None) -> any:
        """
        Get a database instance.
        
        Args:
            db_name: Database name. Uses default if None.
            
        Returns:
            Database instance
            
        Raises:
            RuntimeError: If connection is not initialized
        """
        if not self._initialized or self.client is None:
            raise RuntimeError("MongoDB connection not initialized. Call initialize() first.")
        return self.client[db_name or self.default_db]
    
    def close(self) -> None:
        """Close the MongoDB connection."""
        if self.client is not None:
            self.client.close()
            self._initialized = False
            logger.info("MongoDB connection closed")
    
    async def ping(self) -> bool:
        """
        Ping the MongoDB server to check connection.
        
        Returns:
            True if connection is successful
            
        Raises:
            RuntimeError: If connection is not initialized
        """
        if not self._initialized or self.client is None:
            raise RuntimeError("MongoDB connection not initialized. Call initialize() first.")
        try:
            result = await self.client.admin.command("ping")
            logger.debug("MongoDB ping successful")
            return result.get("ok", 0) == 1
        except Exception as e:
            logger.error(f"MongoDB ping failed: {e}")
            return False


async def set_history(user_id: int, mongodb_manager: MongoDBManager, bot_name: str, collection_name: str) -> str:
    """
    Clear chat history for a user.
    
    Args:
        user_id: User ID to clear history for
        mongodb_manager: MongoDB manager instance
        bot_name: Bot name for database
        collection_name: Collection name
        
    Returns:
        Response message
    """
    db = mongodb_manager.get_database(bot_name)
    collection = db[collection_name]

    try:
        await collection.update_one(
            {"user_id": user_id},
            {"$set": {"language": "Korean"}},
            upsert=True,
        )

        reply_msg = f"Chat history cleared!"
    except Exception as ex:
        logger.error(f"Failed to clear history for user {user_id}: {ex}")
        reply_msg = "😿"
    return reply_msg
