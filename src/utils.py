import asyncio
import logging
import time
from telegram import Update, error
from telegram.constants import ChatAction
from telegram.ext import ContextTypes
from functools import wraps

logger = logging.getLogger(__name__)

def send_action(action):
    def decorator(func):
        @wraps(func)
        async def command_func(update, context, *args, **kwargs):
            await context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=action)
            return await func(update, context,  *args, **kwargs)
        return command_func
    return decorator

async_typing = send_action(ChatAction.TYPING)

