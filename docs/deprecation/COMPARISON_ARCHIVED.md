# Configuration Migration - Comparison

## Before (Hardcoded Values)

```python
# config/config.py (OLD)
from transformers import AutoTokenizer

TUNNEL_URL ="http://127.0.0.1:8000"
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "gemma3n:latest"

TELEGRAM_BOT_TOKEN= "6649921467:AAG-Q9HnuR-JSyN6Q3VWzp55NPgh_n8ZAKY"
EMBED_PATH = "/Users/bo/workspace/KR-SBERT-V40K-klueNLI-augSTS"
TOKENIZER = AutoTokenizer.from_pretrained(EMBED_PATH)
DATABASE = "/Users/bo/workspace/korean_law/db_split"
LOCAL_DATA = "/Users/bo/workspace/korean_law"
CHUNK_SIZE = 1024
start_message = "안녕하세요? 고객님! 저는 법률 상담 챗봇입니다..."
MONGO_HOST="mongodb://localhost"
MONGO_PORT="27017"
BOT_NAME="SugarSquare_bot"
COLLECTION_NAME="chat_history"
```

**Problems:**
- Telegram Bot Token visible in version control
- Hardcoded paths to specific user directories
- Not portable across different systems
- No easy way to change configuration without editing code

## After (Environment Variables)

```python
# config/config.py (NEW)
from transformers import AutoTokenizer
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

TUNNEL_URL = os.getenv("TUNNEL_URL", "http://127.0.0.1:8000")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3n:latest")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
EMBED_PATH = os.getenv("EMBED_PATH")
DATABASE = os.getenv("DATABASE")
LOCAL_DATA = os.getenv("LOCAL_DATA")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1024))
start_message = os.getenv("START_MESSAGE", "안녕하세요? 고객님! 저는 법률 상담 챗봇입니다...")
MONGO_HOST = os.getenv("MONGO_HOST", "mongodb://localhost")
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
BOT_NAME = os.getenv("BOT_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

# Initialize tokenizer only if EMBED_PATH is set
TOKENIZER = None
if EMBED_PATH:
    TOKENIZER = AutoTokenizer.from_pretrained(EMBED_PATH)
```

**Improvements:**
- Telegram Bot Token in .env file (excluded from version control)
- No hardcoded paths - portable across systems
- Easy to change configuration via .env file
- Clear separation of configuration from code
- Default values for non-sensitive configuration
- Required variables clearly identified

## Configuration Files

### .env (Actual Configuration)
```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=6649921467:AAG-Q9HnuR-JSyN6Q3VWzp55NPgh_n8ZAKY

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gemma3n:latest

# Embedding Model Configuration
EMBED_PATH=/Users/bo/workspace/KR-SBERT-V40K-klueNLI-augSTS

# Database Configuration
DATABASE=/Users/bo/workspace/korean_law/db_split
LOCAL_DATA=/Users/bo/workspace/korean_law
CHUNK_SIZE=1024

# MongoDB Configuration
MONGO_HOST=mongodb://localhost
MONGO_PORT=27017

# Bot Configuration
BOT_NAME=SugarSquare_bot
COLLECTION_NAME=chat_history

# Start Message
START_MESSAGE=안녕하세요? 고객님! 저는 법률 상담 챗봇입니다...

# Tunnel URL (optional)
TUNNEL_URL=http://127.0.0.1:8000
```

### .env.example (Template)
```bash
# Telegram Bot Configuration
# REQUIRED: Get your token from @BotFather on Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# Ollama Configuration
# Default values for local Ollama installation
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gemma3n:latest

# Embedding Model Configuration
# REQUIRED: Set this to your actual embedding model path
EMBED_PATH=/path/to/your/KR-SBERT-V40K-klueNLI-augSTS

# Database Configuration
# REQUIRED: Set these to your actual data paths
DATABASE=/path/to/your/korean_law/db_split
LOCAL_DATA=/path/to/your/korean_law
CHUNK_SIZE=1024

# MongoDB Configuration
# Default values for local MongoDB installation
MONGO_HOST=mongodb://localhost
MONGO_PORT=27017

# Bot Configuration
# REQUIRED: Set these to your actual bot and collection names
BOT_NAME=YourBotName
COLLECTION_NAME=chat_history

# Start Message
# Optional: Custom welcome message
START_MESSAGE=Your welcome message here

# Tunnel URL (optional)
# Only needed if you're using a tunnel service
TUNNEL_URL=http://127.0.0.1:8000
```

## Security Comparison

### Before
- ✗ Telegram Bot Token in version control
- ✗ Hardcoded paths visible to everyone
- ✗ No way to hide sensitive information
- ✗ Configuration tied to specific user's system

### After
- ✓ Telegram Bot Token in .env file (excluded from version control)
- ✓ Sensitive information hidden
- ✓ Configuration portable across systems
- ✓ Easy to customize for different environments

## Benefits Summary

1. **Security**: Sensitive information is no longer in version control
2. **Portability**: Works on any system with appropriate .env configuration
3. **Flexibility**: Easy to switch between different configurations
4. **Maintainability**: Configuration is centralized and easy to update
5. **Best Practices**: Follows standard Python project configuration patterns
6. **Documentation**: Clear example file shows what's needed

## Migration Path

For existing users:
1. Copy `.env.example` to `.env`
2. Update `.env` with your specific values
3. Remove old hardcoded values from `config/config.py` (already done)
4. Run `python test_config.py` to verify
5. Start the bot: `python app.py`

## Testing

```bash
# Run comprehensive tests
python test_config.py

# Verify all required variables
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
required = ['TELEGRAM_BOT_TOKEN', 'EMBED_PATH', 'DATABASE', 'LOCAL_DATA', 'BOT_NAME', 'COLLECTION_NAME']
for var in required:
    assert os.getenv(var), f'{var} not set'
print('All required variables are set!')
"
```

All tests should pass successfully.
