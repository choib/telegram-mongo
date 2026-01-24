import logging
import asyncio

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import config
from src.handlers import handle_start, handle_user_id, handle_history, error_handler
from src.agentic_handlers import hybrid_text_chat_handler

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# Set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    """Set up bot commands after initialization."""
    await application.bot.set_my_commands(
        [
            ("user_id", "Get your user ID"),
            ("clear_memory", "Clear your chat history"),
        ]
    )
    
    # Initialize MongoDB connection
    from src.bot import mongodb_manager
    if not mongodb_manager._initialized:
        await mongodb_manager.initialize()
        logger.info("MongoDB connection initialized in post_init")

def main() -> None:
    """Start the Telegram bot."""
    # Create the Application and pass it your bot's token
    application = (
        Application.builder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .read_timeout(180)
        .write_timeout(180)
        .connect_timeout(30)
        .pool_timeout(30)
        .build()
    )
    
    # Register command handlers
    application.add_handler(CommandHandler("start", handle_start))
    application.add_handler(CommandHandler("user_id", handle_user_id))
    application.add_handler(CommandHandler("clear_memory", handle_history))
    
    # Register message handler for text messages - using agentic handler
    application.add_handler(MessageHandler(filters.TEXT, hybrid_text_chat_handler, block=False))
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        timeout=30
    )


if __name__ == "__main__":
    main()
