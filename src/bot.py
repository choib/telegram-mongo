import importlib
import logging
import os
from datetime import datetime

from langchain_core.messages import AIMessage, SystemMessage, HumanMessage, messages_to_dict

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from config import config
# Import the factory that decides which LLM client to use
from src.llm_factory import get_llm_client

# Initialize MongoDB manager
from src.mongo import MongoDBManager
mongodb_manager = MongoDBManager(host=config.MONGO_HOST, port=int(config.MONGO_PORT), default_db=config.BOT_NAME)

# Initialize the selected LLM client (Ollama or Gemini)
llm_client = get_llm_client()

# Initialize Tavily web search
from src.tavily_search import TavilyWebSearch
web_search = TavilyWebSearch(api_key=config.TAVILY_API_KEY, max_results=3)

#settings = importlib.import_module(os.getenv("SETTINGS_FILE"))
system_prompt = """
<<SYS>>You are an American Accounting & Tax Expert. The customer's name is provided below.
Please address the customer by their name followed by 'sir' or 'ma'am' or just the name politely.
Provide professional advice on US GAAP, IRS regulations, tax planning, and financial matters.
Attached below are the conversation history, relevant accounting/tax regulations found via search, and web search results.
Synthesize all this information to answer the new question accurately in English.<</SYS>>
"""
hist_prompt="\n### 과거 질문 목록: "
ai_prompt = "ai: "
extra_prompt = "\n### 관련 자료: "

logger = logging.getLogger(__name__)

async def text_chat_service_template(user_id: int, first_name: str, text: str, msg_date: datetime):
    try:
        chat_history = MongoDBChatMessageHistory(
            collection_name=config.BOT_NAME,
            session_id=str(user_id),
            mongodb_manager=mongodb_manager
        )
        messages = await chat_history.messages
        new_messages = []
        if not messages:
            new_messages.append(
                SystemMessage(
                    content=system_prompt,
                    additional_kwargs={
                        "type": "system",
                        "timestamp": int(msg_date.timestamp()) - 10,
                    },
                )
            )
        new_messages.append(
            HumanMessage(
                content=text,
                additional_kwargs={
                    "type": "text",
                    "timestamp": int(msg_date.timestamp()),
                },
            )
        )
        # Use the selected LLM client to generate a response
        response = await llm_client.generate(
            {
                "messages": messages_to_dict(messages + new_messages)
            }
        )
        new_messages.append(
            AIMessage(
                content=response,
                additional_kwargs={
                    "type": "text",
                    "timestamp": int(msg_date.timestamp()) + 10,
                },
            )
        )
        await chat_history.add_messages(new_messages)
        reply_msg = response
    except Exception as ex:
        logger.error(ex)
        reply_msg = "😿"
    return reply_msg

async def text_chat_service(user_id: int, first_name: str, text: str, msg_date: datetime):
    try:
        chat_history = MongoDBChatMessageHistory(
            collection_name=config.BOT_NAME,
            session_id=str(user_id),
            mongodb_manager=mongodb_manager
        )
        #await chat_history.clear()
        
        # Log conversation history summary for monitoring
        await chat_history.get_conversation_summary(max_length=200)
        
        human_prompt = f"{first_name}: "
        messages = await chat_history.messages
        new_messages = []
        if not messages:
            new_messages.append(
                SystemMessage(
                    content= system_prompt,
                    additional_kwargs={
                        "type": "system",
                        "timestamp": int(msg_date.timestamp()) - 10,
                    },
                )
            )
        new_messages.append(
            HumanMessage(
                content=text,
                additional_kwargs={
                    "type": "text",
                    "timestamp": int(msg_date.timestamp()),
                },
            )
        )
        # Convert messages to list for processing
        messages_list = messages_to_dict(messages)
        
        # Limit chat history to reduce payload size
        # Keep only the most recent 3 exchanges (6 messages total)
        recent_messages = list(messages_list[-6:]) if len(messages_list) >= 6 else list(messages_list)
        
        # Create LLM-powered summary of older messages if they exist
        # Only generate summary for conversations longer than 10 messages
        summary = ""
        if len(messages_list) > 10:
            # Prepare older messages for summarization
            older_messages_text = ""
            for value in messages_list[:-6]:  # Exclude recent messages already in recent_messages
                if value.get('type')=='human':
                    content = value.get('data', {}).get('content', '')
                    older_messages_text += f"\n{first_name}: {content}"
                elif value.get('type')=='ai':
                    content = value.get('data', {}).get('content', '')
                    older_messages_text += f"\nai: {content}"
            
            # Use the selected LLM client to create a concise summary
            summary_prompt = f"""Summarize the following conversation in Korean. Keep it concise (under 200 words) and focus on the key topics, questions, and answers. Do not include greetings or introductory phrases.

Conversation:
{older_messages_text}

Summary (Korean):"""
            
            try:
                logger.info(f"Generating LLM summary for {len(messages_list[:-6])} older messages")
                # Use the selected client's generate method to create a streamed response
                summary_response = ""
                async for chunk in llm_client.generate_stream(summary_prompt):
                    summary_response += chunk
                
                summary = f"\n\n### Previous conversation summary:\n{summary_response}\n\n---\n"
                logger.info(f"Generated summary: {len(summary)} characters")
                # Log the summary content for monitoring
                logger.info(f"LLM Summary Content: {summary_response[:500]}..." if len(summary_response) > 500 else f"LLM Summary Content: {summary_response}")
            except Exception as e:
                logger.error(f"Failed to generate LLM summary: {e}")
                # Fallback to simple truncation if LLM summary fails
                summary = "\n\n### Previous conversation summary:\n"
                for value in messages_list[:-10]:
                    if value.get('type')=='human':
                        content = value.get('data', {}).get('content', '')
                        if len(content) > 100:
                            content = content[:100] + '...'
                        summary += f"\n- User: {content}"
                    elif value.get('type')=='ai':
                        content = value.get('data', {}).get('content', '')
                        if len(content) > 100:
                            content = content[:100] + '...'
                        summary += f"\n- AI: {content}"
                logger.info(f"Fallback summary generated: {len(summary)} characters")
                logger.info(f"Fallback Summary Content: {summary[:500]}..." if len(summary) > 500 else f"Fallback Summary Content: {summary}")
        else:
            # For short conversations, just use simple truncation without LLM
            logger.info(f"Short conversation ({len(messages_list)} messages), skipping LLM summary")
        
        # Build recent history from recent messages using list for efficiency
        hist_lines = []
        for value in recent_messages:
            if value.get('type')=='human':
                hist_lines.append(human_prompt + value.get('data', {}).get('content', ''))
            elif value.get('type')=='ai':
                hist_lines.append(ai_prompt + value.get('data', {}).get('content', ''))
        
        # Add summary to the beginning of history
        if summary:
            hist = summary + "\n" + "\n".join(hist_lines)
        else:
            hist = "\n".join(hist_lines)
        
        # Get current human message
        human = ""
        for value in messages_to_dict(new_messages):
            if value.get('type')=='human':
                human =  value.get('data', {}).get('content', '')
        
        # Log payload size optimization
        summary_type = "LLM-powered summary" if summary and '### Previous conversation summary:' in summary else "none"
        logger.info(f"Chat history optimization: {len(messages_list)} total messages -> {len(recent_messages)} recent + {summary_type}")
        
        qna = hist + human #question +
        related = ans_retriever.invoke(qna) #inspect_re
        
        # Use list for efficient joining instead of string concatenation
        doc_contents = []
        for doc in related:
            doc_contents.append(doc.page_content)
        extra_input = "\n".join(doc_contents)

        # Get web search results - only for queries that likely need recent information
        web_results = ""
        try:
            # Analyze query to determine if web search is needed
            # Skip web search for clearly legal document queries
            query_lower = human.lower()
            accounting_keywords = ['accounting', 'tax', 'gaap', 'irs', 'cpa', 'audit', 'finance', 'closing', '회계', '세무']
            
            needs_web_search = True
            for keyword in accounting_keywords:
                if keyword in query_lower:
                    needs_web_search = False
                    logger.info(f"Skipping web search for accounting query containing: {keyword}")
                    break
            
            if needs_web_search:
                # Initialize web search if not already initialized
                if not web_search._initialized:
                    await web_search.initialize()
                
                if web_search.client is not None:
                    web_results = await web_search.get_search_summary(human)
                    logger.info(f"Web search results included in payload. Length: {len(web_results)} characters")
                    
                    # Log that web search was successful
                    logger.info(f"Web search completed successfully for query: '{human[:100]}...'")
                else:
                    logger.warning("Web search client not initialized, skipping web search")
            else:
                logger.info(f"Skipped web search for legal query: '{human[:100]}...'")
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            # Even if web search fails, continue with the response
        if hist == "":
            # payload = {"prompt": system_prompt + human}
            payload = "<s>" + system_prompt + f"## 고객 이름: {first_name}\n" + extra_prompt + extra_input +  human_prompt + human + web_results + "<s>"
        else:
            payload = "<s>" + system_prompt + f"## 고객 이름: {first_name}\n" + hist_prompt + hist + extra_prompt + extra_input+ human_prompt + human + web_results + "<s>"

        
        logger.info(f"Generated payload for LLM. Total length: {len(payload)} characters")
        
        # Calculate original payload size for comparison using list for efficiency
        original_hist_lines = []
        for value in messages_to_dict(messages):
            if value.get('type')=='human':
                original_hist_lines.append(human_prompt + value.get('data', {}).get('content', ''))
            elif value.get('type')=='ai':
                original_hist_lines.append(ai_prompt + value.get('data', {}).get('content', ''))
        
        # Calculate size reduction
        if original_hist_lines:
            original_hist = "\n".join(original_hist_lines)
            original_payload = "<!" + system_prompt + f"## 고객 이름: {first_name}\n" + hist_prompt + original_hist + extra_prompt + extra_input+ human_prompt + human + web_results + "<!"
            size_reduction = len(original_payload) - len(payload)
            reduction_percent = (size_reduction / len(original_payload)) * 100 if len(original_payload) > 0 else 0
            logger.info(f"Payload size optimization: Reduced from {len(original_payload)} to {len(payload)} characters ({reduction_percent:.1f}% reduction)")
        
        if summary and '### Previous conversation summary:' in summary:
            logger.info(f"Summary type: LLM-powered summary")
            # Extract and log summary content for monitoring
            summary_content = summary.replace('\n\n### Previous conversation summary:\n', '').replace('\n\n---\n', '')
            logger.info(f"Summary content length: {len(summary_content)} characters")
            logger.info(f"Summary content preview: {summary_content[:500]}..." if len(summary_content) > 500 else f"Summary content preview: {summary_content}")
        else:
            logger.info(f"Summary type: none (short conversation)")
        
        response = ""
        # Use the selected LLM client to generate a response (non‑streaming for simplicity)
        response = await llm_client.generate(payload)
        new_messages.append(
            AIMessage(
                content=response,
                additional_kwargs={
                    "type": "text",
                    "timestamp": int(msg_date.timestamp()) + 10,
                },
            )
        )
        await chat_history.add_messages(new_messages)
        reply_msg = response
        
    except Exception as ex:
        logger.error(ex)
        reply_msg = "😿"
    return reply_msg

lines_read: 357
was_truncated: False