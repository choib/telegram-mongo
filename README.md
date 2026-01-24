# ⚖️ Korean Law Expert Bot

A specialized Telegram bot leveraging an agentic architecture and RAG (Retrieval-Augmented Generation) to provide expert-level assistance on Korean laws and legal documents.

## 🚀 Core Features

- **Agentic Legal Reasoning**: Multi-agent system capable of analyzing legal queries and determining the need for local RAG retrieval vs. real-time web search.
- **High-Fidelity RAG Pipeline**: Specialized retrieval focused on a curated corpus of 200+ Korean law files.
- **Context-Aware Processing**: Intelligent document splitting that maintains legal hierarchy (Articles, Paragraphs) for precise retrieval.
- **Automated Law Updates**: CLI tools to fetch the latest revisions from the National Law Information Center (`law.go.kr`).
- **Confidence Scoring**: Built-in verification to ensure quality and relevance of returned legal information.

## 📂 Project Structure

```bash
telegram-mongo/
├── config/             # Environment-specific configuration
├── data/               # Source data (PDF/Text)
├── db/                 # Vector stores (Chroma)
├── docs/               # Detailed technical documentation
├── scripts/            # Development and maintenance utilities
├── src/                # Core application logic
│   ├── agentic_handlers.py # AI reasoning flow
│   ├── context_aware_splitter.py # Legal-aware chunker
│   └── ...
├── app.py              # Main bot entry point
├── rag.py              # RAG management CLI
└── scripts/update_laws.py # Law update engine
```

## 🛠️ Management CLI

### RAG Database Management
Regenerate or update the vector store directly:
```bash
python3 rag.py --rebuild          # Force rebuild the database
python3 rag.py --test "헌법이란?"  # Test retrieval
```

### Law Repository Update
Fetch latest laws from the official API:
```bash
python3 scripts/update_laws.py   # Update all laws in scripts/law_names.txt
```

## 🚀 Deployment

### Prerequisites
- Python 3.11+
- [Ollama](https://ollama.ai/) or Gemini API Key
- [Tavily API Key](https://tavily.com/) for web search

#### 🤖 Setting up your Telegram Bot
1. Search for **@BotFather** on Telegram.
2. Send `/newbot` and follow the instructions to create your bot.
3. Save the **API Token** provided and paste it into `TELEGRAM_BOT_TOKEN` in your `.env` file.

#### 🍃 Setting up MongoDB
The bot requires MongoDB for session persistence.
- **Local Setup**: Install MongoDB Community Edition and ensure it's running on `localhost:27017`.
- **Cloud Setup**: Use [MongoDB Atlas](https://www.mongodb.com/cloud/atlas).
- Update `MONGO_HOST` and `MONGO_PORT` in your `.env` file accordingly.

### Installation
1. Clone the repository and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure your `.env` file based on `.env.example`.
3. Initialize the database:
   ```bash
   python3 rag.py --rebuild
   ```
4. Start the bot:
   ```bash
   python3 app.py
   ```

## 📚 Technical Documentation
Detailed guides on architecture, feature implementations, and migration are available in the `docs/` directory.

---
**Status**: Production Ready ✅
**Last Updated**: January 2026
