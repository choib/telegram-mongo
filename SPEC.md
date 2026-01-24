# ⚖️ Korean Law Expert Bot Specification

This document serves as the project's technical specification, defining the architecture, core data models, and functional requirements.

## 1. System Overview
The **Korean Law Expert Bot** is an agentic RAG (Retrieval-Augmented Generation) system built on **LangGraph**. It is designed to provide expert-level legal assistance by combining specialized local document retrieval with real-time web search capabilities.

## 2. Technical Stack
- **Language**: Python 3.11+
- **Agent Framework**: [LangGraph](https://langchain-ai.github.io/langgraph/)
- **Bot Interface**: [python-telegram-bot](https://python-telegram-bot.org/)
- **LLM Providers**:
  - Cloud: **Google Gemini API** (Gemini 3 Flash Preview)
  - Local: **Ollama** (Gemma 3:4b)
- **Database**:
  - Vector Store: **ChromaDB** (for RAG)
  - Message Store: **MongoDB** (for session persistence)
- **Search API**: [Tavily AI](https://tavily.com/)

## 3. Core Components

### 3.1 Agentic Architecture (Graph Flow)
The system uses a directed graph to orchestrate reasoning:
1. **Analyze Node**: Augments the user's query using conversation history to improve retrieval.
2. **Judge Augmentation Node**: Assesses if the query is clear enough or requires user clarification.
3. **Judge Node**: Decides which specialized agents (RAG, WebSearch, or both) are required.
4. **Retrieval Node**: Executes parallel retrieval from vectorized law files and/or the web.
5. **Combine Node**: Synthesizes all gathered information into a professional legal response.

### 3.2 Data Models

#### Vector Database (ChromaDB)
- **Collection**: `law_vector_store`
- **Metadata**: `title` (Law Name), `reference` (Article/Article Number), `type` (Paragraph/Item)
- **Splitting Strategy**: Context-Aware (Preserves legal hierarchy).

#### Session Persistence (MongoDB)
- **Database**: `SugarSquare_bot` (Configurable)
- **Collection**: `chat_history`
- **Schema**:
  - `session_id`: (String) Discord/Telegram User ID
  - `history`: (JSON) LangChain-compatible message objects (`HumanMessage`, `AIMessage`)

## 4. Operational Requirements

### 4.1 Response Constraints
- **Maximum Execution Time**: 300 seconds for complex synthesis.
- **LLM Output Limit**: 8,192 tokens.
- **Telegram Message Splitting**: Automatic splitting of responses exceeding 4,096 characters.

### 4.2 Security & Compliance
- **PII Protection**: Conversations are private and stored in a user-managed MongoDB instance.
- **Secrets Management**: Sensitive keys are loaded via `.env` and excluded from repository tracking.

## 5. Maintenance CLI
- **`rag.py`**: Manages vector database lifecycle (rebuild, test).
- **`update_laws.py`**: Automated fetcher for the National Law Information Center (`law.go.kr`).
