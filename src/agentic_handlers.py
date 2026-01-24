"""
Agentic handlers for the Telegram bot.
This module provides handlers that use the agentic architecture.
"""

import logging
from typing import List, Dict, Any
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction
from datetime import datetime

from src.agents import run_agent_workflow, stream_agent_workflow, judging_agent
from src.history import MongoDBChatMessageHistory
from src.mongo import MongoDBManager
from config import config
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)

# Initialize MongoDB manager
mongodb_manager = MongoDBManager(host=config.MONGO_HOST, port=int(config.MONGO_PORT), default_db=config.BOT_NAME)


async def update_progress_animation(context, chat_id, message_id, progress_steps):
    """
    Update the progress message periodically to show thinking animation.
    
    Args:
        context: Telegram context
        chat_id: Chat ID
        message_id: Message ID to update
        progress_steps: List of progress messages to cycle through
    """
    import asyncio
    
    try:
        for step in progress_steps:
            # Update the message with current progress
            await context.bot.edit_message_text(
                text=f"{config.UI['searching']}\n\n{step}",
                chat_id=chat_id,
                message_id=message_id,
                #parse_mode='MarkdownV2',
            )
            # Wait for 3 seconds before next update
            await asyncio.sleep(3)
    except Exception as e:
        logger.debug(f"Progress animation cancelled or error: {e}")
        pass


def format_response_with_markdown(text: str) -> str:
    """
    Format text with MarkdownV2 for Telegram.
    
    This function:
    1. Converts common markdown (like **bold**) to Telegram's MarkdownV2 syntax.
    2. Escapes literal special characters while preserving markdown entities.
    3. Handles headers and lists by converting them to bold text or properly escaped lists.
    
    Args:
        text: The input text to format
        
    Returns:
        Formatted text with MarkdownV2 syntax
    """
    import re

    # 1. Pre-processing: Handle LLM specific formatting
    
    # Handle bold-italic first (***text***)
    text = re.sub(r'\*\*\*(.*?)\*\*\*', r'PROTECT_BOLD_ITALIC_START\1PROTECT_BOLD_ITALIC_END', text)
    
    # Convert headers (### Header) to Bold
    text = re.sub(r'^#{1,6}\s+(.+)$', r'PROTECT_BOLD_START\1PROTECT_BOLD_END', text, flags=re.MULTILINE)
    
    # Convert **bold** to *bold* (MarkdownV2 uses single asterisk for bold)
    text = re.sub(r'\*\*(.*?)\*\*', r'PROTECT_BOLD_START\1PROTECT_BOLD_END', text)
    
    # Handle single *italic* if present
    # We use a strictly defined pattern to avoid matching lists
    text = re.sub(r'(?<!\*)\*([^\*\s][^\*]*?[^\*\s])\*(?!\*)', r'PROTECT_ITALIC_START\1PROTECT_ITALIC_END', text)

    # 2. Character Escaping
    special_chars = r'_*[]()~`>#+-=|{}.!\\'
    
    # Protect links: [text](url)
    links = []
    def save_link(match):
        links.append(match.group(0))
        return f"PROTECT_LINK_{len(links)-1}_"
    
    text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', save_link, text)
    
    # Protect code blocks and inline code
    code_entities = []
    def save_code(match):
        code_entities.append(match.group(0))
        return f"PROTECT_CODE_{len(code_entities)-1}_"
    
    text = re.sub(r'```.*?```', save_code, text, flags=re.DOTALL)
    text = re.sub(r'`[^`]+`', save_code, text)

    # Escape all special characters in the text
    def escape_chars(t):
        # IMPORTANT: Escape backslash FIRST to avoid double escaping problems
        # like turning \. into \\. (which is a literal \ and an unescaped .)
        t = t.replace('\\', '\\\\')
        for char in special_chars.replace('\\', ''):
            t = t.replace(char, '\\' + char)
        return t

    text = escape_chars(text)

    # 3. Unprotect and finalize
    
    # Restore and escape link components
    for i, link in enumerate(links):
        match = re.match(r'\[([^\]]+)\]\(([^\)]+)\)', link)
        if match:
            link_text = escape_chars(match.group(1))
            link_url = match.group(2)
            link_url = link_url.replace('(', '\\(').replace(')', '\\)')
            text = text.replace(f"PROTECT\\_LINK\\_{i}\\_", f"[{link_text}]({link_url})")

    # Restore code entities
    for i, code in enumerate(code_entities):
        text = text.replace(f"PROTECT\\_CODE\\_{i}\\_", code)

    # Restore temporary markers with MarkdownV2 syntax
    # Bold-Italic: *_text_*
    text = text.replace('PROTECT\\_BOLD\\_ITALIC\\_START', '*_').replace('PROTECT\\_BOLD\\_ITALIC\\_END', '_*')
    # Bold: *text*
    text = text.replace('PROTECT\\_BOLD\\_START', '*').replace('PROTECT\\_BOLD\\_END', '*')
    # Italic: _text_
    text = text.replace('PROTECT\\_ITALIC\\_START', '_').replace('PROTECT\\_ITALIC\\_END', '_')

    return text


def split_message(text: str, max_part_len: int = 4090) -> List[str]:
    """
    Split a long message into multiple parts for Telegram, 
    ensuring each part is valid MarkdownV2 if possible.
    
    This is a simpler approach that splits by paragraphs/sections 
    and tries to keep markdown entities balanced.
    """
    if len(text) <= max_part_len:
        return [text]
        
    parts = []
    current_part = ""
    
    # Split by double newlines to preserve paragraphs
    lines = text.split('\n')
    
    for line in lines:
        if len(current_part) + len(line) + 1 > max_part_len:
            if current_part:
                parts.append(current_part.strip())
                current_part = line + '\n'
            else:
                # Singular line is too long, split it forcefully
                while len(line) > max_part_len:
                    parts.append(line[:max_part_len])
                    line = line[max_part_len:]
                current_part = line + '\n'
        else:
            current_part += line + '\n'
            
    if current_part:
        parts.append(current_part.strip())
        
    # Final safety check: Close any open markdown tags in each part
    # (Simplified: just use safe_truncate logic to fix each part)
    final_parts = []
    for part in parts:
        final_parts.append(safe_truncate(part, max_part_len, suffix=""))
        
    return final_parts

def safe_truncate(text: str, max_len: int, suffix: str = "\\.\\.\\. \\[truncated\\]") -> str:
    """
    Truncate a string while ensuring:
    1. We don't end on a trailing backslash (breaking an escape sequence).
    2. Any open markdown entities (bold, italic, code) are closed before the suffix.
    """
    if len(text) <= max_len:
        return text
    
    # Reserve space for suffix + potential closing tags (*, _, `, ```)
    # 10 characters buffer for closing tags is plenty
    limit = max_len - len(suffix) - 10
    
    # Initial truncation
    target_pos = limit
    
    # Ensure we don't end with an odd number of trailing backslashes
    while target_pos > 0:
        backslash_count = 0
        p = target_pos - 1
        while p >= 0 and text[p] == '\\':
            backslash_count += 1
            p -= 1
        
        if backslash_count % 2 == 0:
            break
        target_pos -= 1
        
    truncated = text[:target_pos]
    
    # Track open entities in the truncated part
    stack = []
    i = 0
    while i < len(truncated):
        if i > 0 and truncated[i-1] == '\\':
            # This character is escaped, check if the backslash itself is escaped
            bs_count = 0
            p = i - 1
            while p >= 0 and truncated[p] == '\\':
                bs_count += 1
                p -= 1
            if bs_count % 2 != 0:
                # Escaped
                i += 1
                continue
        
        char = truncated[i]
        if char == '*':
            if stack and stack[-1] == '*':
                stack.pop()
            else:
                stack.append('*')
        elif char == '_':
            if stack and stack[-1] == '_':
                stack.pop()
            else:
                stack.append('_')
        elif char == '`':
            if truncated[i:i+3] == '```':
                if stack and stack[-1] == '```':
                    stack.pop()
                else:
                    stack.append('```')
                i += 2
            else:
                if stack and stack[-1] == '`':
                    stack.pop()
                else:
                    stack.append('`')
        i += 1
    
    # Generate closing tags in reverse order
    closing_tags = ""
    while stack:
        closing_tags += stack.pop()
        
    return truncated + closing_tags + suffix


async def agentic_text_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Initialize the connection on first use
    if not mongodb_manager._initialized:
        await mongodb_manager.initialize()
    """
    Agentic text chat handler using Langgraph architecture.
    
    This handler:
    1. Shows typing action
    2. Retrieves conversation history
    3. Runs the agent workflow
    4. Assesses confidence and asks supplement questions if needed
    5. Sends the response
    """
    try:
        # Show typing action to indicate the bot is processing
        await context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
        
        # Send thinking message first
        thinking_msg = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"{config.UI['searching']}\n\n{config.UI['progress_prefix']}0%",
            reply_to_message_id=update.message.id,
        )
        
        # Get user information
        user_id = update.message.from_user.id
        first_name = update.message.from_user.first_name
        text = update.message.text
        msg_date = update.message.date
        
        # Get conversation history for context
        chat_history = MongoDBChatMessageHistory(
            collection_name=config.BOT_NAME,
            session_id=str(user_id),
            mongodb_manager=mongodb_manager
        )
        
        # Log conversation history summary for monitoring
        await chat_history.get_conversation_summary(max_length=200)
        
        # Get recent messages for context
        messages = await chat_history.messages
        if not messages:
            logger.info("Conversation history is empty.")
        else:
            logger.info(f"Retrieved {len(messages)} messages from history for user {user_id}")
            
        context_text = ""
        
        # Convert messages to text format for context
        for msg in messages[-10:]:  # Use last 10 messages as context
            if msg.type == 'human':
                context_text += f"\n--- User: {msg.content}"
            elif msg.type == 'ai':
                context_text += f"\n--- AI: {msg.content}"
            else:
                context_text += f"\n--- {msg.type.capitalize()}: {msg.content}"
        
        # Mapping for progress messages
        PROGRESS_MAPPING = {
            "analyze": "🔍 Understanding context...",
            "judge_augmentation": "⚖️ Evaluating query quality...",
            "judge": "🤔 Analyzing your question...",
            "retrieval": "📚 Searching for relevant information...",
            "combine": "✍️ Crafting your response...",
            "clarify": "📢 Requesting clarification..."
        }
        
        last_progress_msg = ""
        result = {}
        
        # Show initial searching message
        await context.bot.edit_message_text(
            text=f"{config.UI['searching']}\n\n{PROGRESS_MAPPING['judge']}",
            chat_id=update.effective_chat.id,
            message_id=thinking_msg.id
        )

        # Run agent workflow with streaming events
        async for event in stream_agent_workflow(
            query=text,
            context=context_text if context_text else "No previous context"
        ):
            event_type = event["event"]
            # Look for node execution events from langgraph
            if event_type == "on_chain_start":
                node_name = event.get("metadata", {}).get("langgraph_node")
                if node_name in PROGRESS_MAPPING:
                    new_msg = PROGRESS_MAPPING[node_name]
                    if new_msg != last_progress_msg:
                        try:
                            # Update the thinking message with current progress
                            await context.bot.edit_message_text(
                                text=f"{config.UI['searching']}\n\n{new_msg}",
                                chat_id=update.effective_chat.id,
                                message_id=thinking_msg.id
                            )
                            last_progress_msg = new_msg
                        except Exception as e:
                            logger.debug(f"Error updating progress message: {e}")
            # Capture the final output from the entire graph
            if event_type == "on_chain_end":
                output = event.get("data", {}).get("output", {})
                if isinstance(output, dict) and "final_response" in output:
                    result = output
                    logger.debug(f"Captured final response from chain: {event.get('name')}")
            
        # Capture the final output
        logger.info("Agent workflow loop finished.")
        
        # Get the final response
        reply_msg = result.get('final_response')
        if not reply_msg:
            logger.warning("No final_response found in result. Using fallback.")
            reply_msg = config.UI.get('error_msg', "An error occurred.")
        
        logger.info(f"Final response captured. Length: {len(reply_msg)} chars")
        
        # Assess confidence in the answer OR use quality score from augmentation
        quality_low = result.get('quality_low', False)
        augmentation_score = result.get('augmentation_quality', {}).get('score', 0)
        
        if quality_low:
            logger.info(f"Using augmentation quality score for clarification: {augmentation_score}%")
            confidence_score = augmentation_score
            confidence_reasoning = "Query quality low (augmentation check)"
        else:
            # Assess confidence in the answer
            logger.info("Assessing confidence...")
            confidence_assessment = await judging_agent.assess_confidence(
                query=text,
                answer=reply_msg,
                context=context_text if context_text else ""
            )
            confidence_score = confidence_assessment.get('confidence_score', 0)
            confidence_reasoning = confidence_assessment.get('reasoning', 'None')
            
        logger.info(f"Confidence score: {confidence_score}%")
        logger.info(f"Confidence reasoning: {confidence_reasoning}")
        
        # Check for supplement questions from the augmentation quality check
        supplement_questions = result.get('supplement_questions', [])
        
        # Prepare messages for history
        from langchain_core.messages import HumanMessage, AIMessage
        
        # Build full unformatted message
        full_raw_msg = reply_msg if reply_msg else ""
        
        if confidence_score < config.CONFIDENCE_THRESHOLD or supplement_questions:
            logger.info(f"Low confidence ({confidence_score}%) or supplement questions generated")
            
            # If supplement questions were generated from quality check, use those
            if not supplement_questions and confidence_score < config.CONFIDENCE_THRESHOLD:
                # Generate supplement questions only if confidence is low and not already generated
                confidence_assessment_data = {"confidence_score": confidence_score, "reasoning": confidence_reasoning}
                supplement_questions = await judging_agent.generate_supplement_questions(
                    query=text,
                    answer=reply_msg,
                    confidence_assessment=confidence_assessment_data
                )
            
            # Format supplement questions message
            questions_text = "\n\n".join([f"{i+1}. {q}" for i, q in enumerate(supplement_questions)])
            warning_text = f"{config.UI['low_confidence_warning']} ({confidence_score}%)\.\n\n{config.UI['support_msg']}\n\n{questions_text}"
            
            if full_raw_msg:
                full_raw_msg += "\n\n" + warning_text
            else:
                full_raw_msg = warning_text
        
        # Format the entire message with MarkdownV2
        formatted_msg = format_response_with_markdown(full_raw_msg)
        
        # Split message into multiples if it exceeds Telegram limits
        msg_parts = split_message(formatted_msg)
        
        # Edit the thinking message with the first part
        await context.bot.edit_message_text(
            text=msg_parts[0],
            chat_id=update.effective_chat.id,
            message_id=thinking_msg.id,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        
        # Send remaining parts as new messages
        for part in msg_parts[1:]:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=part,
                parse_mode=ParseMode.MARKDOWN_V2,
            )

        # ALWAYS Store the conversation in history 
        new_messages = [
            HumanMessage(
                content=text,
                additional_kwargs={
                    "type": "text",
                    "timestamp": int(msg_date.timestamp()),
                },
            ),
            AIMessage(
                content=reply_msg, # Store the raw reply for future context
                additional_kwargs={
                    "type": "text",
                    "timestamp": int(msg_date.timestamp()) + 10,
                    "confidence_score": confidence_score
                },
            )
        ]
        
        await chat_history.add_messages(new_messages)
        
        # Log the interaction
        logger.info(f"User {user_id} ({first_name}): {text[:50]}...")
        logger.info(f"Confidence: {confidence_score}%")
        logger.info(f"Response saved to history. Length: {len(reply_msg)} characters")
        logger.info(f"Agent flow: {result.get('agent_flow', [])}")
        logger.info(f"Web search was used: {'WebSearch' in result.get('agent_flow', [])}")
        
    except Exception as ex:
        logger.error(f"Error in agentic handler: {ex}")
        try:
            # Format error message correctly
            error_msg = format_response_with_markdown(config.UI["error_msg"])
            
            await context.bot.edit_message_text(
                text=error_msg,
                chat_id=update.effective_chat.id,
                message_id=thinking_msg.id,
                parse_mode=ParseMode.MARKDOWN_V2,
            )
        except Exception as edit_ex:
            logger.error(f"Error editing error message: {edit_ex}")
            # If we can't edit the thinking message, send a new error message
            error_msg = format_response_with_markdown("😿 An error occurred while processing your request.")
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=error_msg,
                reply_to_message_id=update.message.id,
                parse_mode=ParseMode.MARKDOWN_V2,
            )


async def hybrid_text_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Hybrid handler that can switch between agentic and traditional modes.
    
    This provides a fallback mechanism if the agentic approach fails.
    """
    try:
        # First try agentic approach
        await agentic_text_chat_handler(update, context)
    except Exception as ex:
        logger.error(f"Agentic handler failed, falling back to traditional: {ex}")
        
        # Fall back to traditional handler
        from src.bot import text_chat_service
        
        user_id = update.message.from_user.id
        first_name = update.message.from_user.first_name
        text = update.message.text
        msg_date = update.message.date
        
        # Show typing action
        await context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
        
        # Send thinking message
        thinking_msg = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="💭 Searching for relevant information...",
            reply_to_message_id=update.message.id,
        )
        
        # Get response
        reply_msg = await text_chat_service(user_id, first_name, text, msg_date)
        
        # Use the centralized formatter
        formatted_msg = format_response_with_markdown(reply_msg)
        
        # Edit thinking message with response
        await context.bot.edit_message_text(
            text=formatted_msg,
            chat_id=update.effective_chat.id,
            message_id=thinking_msg.id,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        
        logger.info(f"Fallback to traditional handler successful for user {user_id}")
