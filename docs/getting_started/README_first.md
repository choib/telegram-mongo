# Getting Started – telegram-mongo

A minimal step‑by‑step guide to run the bot locally.

## Prerequisites
- Python 3.11+
- Docker (optional, for local MongoDB)
- An environment file (`.env`) – see `docs/config/.env.example`.

## Installation
```bash
git clone https://github.com/yourorg/telegram-mongo.git
cd telegram-mongo
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration
1. Copy the example file: `cp .env.example .env`  
2. Edit `.env` with your Telegram Bot Token, Ollama endpoint, MongoDB URI, etc.

## Run Locally
```bash
python app.py          # Starts the bot in foreground
# or, for production‑style:
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## Quick Test
```bash
pytest -q               # Runs the test suite
```
If all tests pass you’re ready to start building!

---

*For deeper configuration details see `docs/config/README.md` (generated from `config/config.py`).*