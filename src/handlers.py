import importlib
import logging
import os

from telegram import Update
from telegram.ext import ContextTypes
from config import config
from src.utils import async_typing
from src.bot import text_chat_service, mongodb_manager
from src.mongo import set_history 
from telegram.constants import ChatAction, ParseMode
from src.history import MongoDBChatMessageHistory
import asyncio

logger = logging.getLogger(__name__)

@async_typing
async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=config.START_MESSAGE,
        reply_to_message_id=update.message.id,
    )

@async_typing
async def handle_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=str(update.message.from_user.id),
        reply_to_message_id=update.message.id,
    )

@async_typing
async def handle_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_history = MongoDBChatMessageHistory(
        collection_name=config.BOT_NAME,
        session_id=str(update.message.from_user.id),
        mongodb_manager=mongodb_manager
    )
    await chat_history.clear()

    reply_msg = await set_history(
        user_id=update.message.from_user.id,
        mongodb_manager=mongodb_manager,
        bot_name=config.BOT_NAME,
        collection_name=config.BOT_NAME
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=reply_msg,
        reply_to_message_id=update.message.id,
    )

@async_typing
async def text_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Show typing action to indicate the bot is processing
    await context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
    
    # Send thinking message first
    thinking_msg = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="💭 관련 자료를 검색 중입니다...",
        reply_to_message_id=update.message.id,
    )
    
    # Get the actual response from the service
    reply_msg = await text_chat_service(
        update.message.from_user.id, update.message.from_user.first_name, update.message.text, update.message.date
    )
    
    # Format response with markdown
    from src.agentic_handlers import format_response_with_markdown
    formatted_msg = format_response_with_markdown(reply_msg)
    
    # Edit the thinking message with the actual response using MarkdownV2
    await context.bot.edit_message_text(
        text=formatted_msg,
        chat_id=update.effective_chat.id,
        message_id=thinking_msg.id,
        parse_mode=ParseMode.MARKDOWN_V2,
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    from telegram.error import NetworkError, Conflict
    
    # Check if the error is a transient network error or a conflict
    if isinstance(context.error, (NetworkError, Conflict)):
        logger.warning(f"Transient error: {context.error}")
        return

    # Log the error before we do anything else, so we can see it even if something breaks here.
    logger.error("Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python traceback list of strings
    import traceback
    import html
    import json

    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    # Build the message with some information and the traceback
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    # Finally, send the message
    # Note: In a production bot, you might want to send this to a developer chat instead of the user
    if isinstance(update, Update) and update.effective_chat:
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="😿 *An error occurred while processing your request\\.* I have logged the details and will look into it\\.",
                parse_mode=ParseMode.MARKDOWN_V2
            )
        except Exception as e:
            logger.error(f"Failed to send error notification to user: {e}")
