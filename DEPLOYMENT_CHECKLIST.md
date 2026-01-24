# 📋 Deployment Checklist: Korean Law Expert Bot

Follow this guide to transition the Korean Law Expert Bot to a production environment.

## 🏗️ Phase 1: Environment Preparation

### 1. Infrastructure
- [ ] **Python 3.11+**: Ensure the production environment has the correct Python version.
- [ ] **MongoDB**: Verify the MongoDB instance is reachable and `MONGO_HOST`/`MONGO_PORT` are set in `.env`.
- [ ] **Ollama/Gemini**: Ensure the LLM provider is active and accessible via the configured host/API key.

### 2. Dependencies
- [ ] **pip Install**: `pip install -r requirements.txt`
- [ ] **Environment Variables**: `cp .env.example .env` and configure all required keys (TAVILY, GEMINI/Ollama, etc.).

## 📦 Phase 2: Data & RAG Initialization

### 1. Law Corpus
- [ ] **Master List**: Verify `law_names.txt` contains the desired set of laws.
- [ ] **Data Sync**: Run `python3 update_laws.py` to ensure local text files are the latest versions from `law.go.kr`.

### 2. Vector Store
- [ ] **Chroma Rebuild**: Run `python3 rag.py --rebuild`.
- [ ] **Verification**: Run `python3 rag.py --test "헌법"` to confirm retrieval is functional.

## 🚀 Phase 3: Bot Launch

### 1. Startup
- [ ] **Entry Point**: Launch the bot with `python3 app.py`.
- [ ] **Log Check**: Monitor `INFO` logs for successful MongoDB connection and Telegram initialization.

### 2. Functional Verification
- [ ] Send `/start` to the bot on Telegram.
- [ ] Test a few legal queries to verify RAG and Agentic Reasoning.
- [ ] Test `/clear_memory` to ensure session management is working.

## 🛠️ Phase 4: Maintenance & Monitoring

- [ ] **Process Management**: Use `pm2`, `systemd`, or `supervisord` to keep `app.py` running.
- [ ] **Backup**: Schedule regular backups for the `db/` (Chroma) and MongoDB collections.
- [ ] **Updates**: Periodically run `update_laws.py` followed by `rag.py --rebuild` to keep the bot's knowledge current.

---
**Version**: 1.1
**Last Verified**: Jan 2026
