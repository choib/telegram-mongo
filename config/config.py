from transformers import AutoTokenizer
from dotenv import load_dotenv
import os
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Config")

# Get project root and load .env from there explicitly
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / '.env'
load_dotenv(dotenv_path=ENV_PATH)

# Basic Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Feature Configuration
BOT_PERSONALITY = os.getenv("BOT_PERSONALITY")
CONFIDENCE_THRESHOLD = int(os.getenv("CONFIDENCE_THRESHOLD"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1024))

# Persistence
MONGO_HOST = os.getenv("MONGO_HOST", "mongodb://localhost")
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
BOT_NAME = os.getenv("BOT_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

# LLM Provider Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER")  # "ollama" or "gemini"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")

# Personality Registry
PERSONALITIES = {
    "accounting": {
        "role": "American Accounting & Tax Expert",
        "language": "en",
        "embed_path": "sentence-transformers/all-MiniLM-L6-v2",
        "database": "./db/pdf_store",
        "local_data": "./data/pdfs",
        "start_message": "Hello! I am your American Accounting & Tax Expert. I can assist you with US GAAP, tax filings, IRS regulations, and more. How can I help you today?",
        "ui": {
            "searching": "💭 Searching for relevant information...",
            "progress_prefix": "🔍 Progress: ",
            "thinking": "🤔 Reasoning...",
            "low_confidence_warning": "⚠️ *Note: The confidence score for this answer is low*",
            "support_msg": "Providing more details could help me give you a more accurate answer:",
            "error_msg": "😿 An error occurred while processing your request.",
            "web_search_header": "### Web Search Results",
            "web_search_no_results": "- No relevant web search results found."
        }
    },
    "legal": {
        "role": "Korean Law Expert",
        "language": "ko",
        "embed_path": "/Users/bo/workspace/KR-SBERT-V40K-klueNLI-augSTS",
        "database": "/Users/bo/workspace/korean_law/db_split",
        "local_data": "/Users/bo/workspace/korean_law",
        "start_message": "안녕하세요! 한국 법률 전문가 비서입니다. 법률 상담, 판례 검색 등을 도와드릴 수 있습니다. 무엇을 도와드릴까요?",
        "ui": {
            "searching": "💭 관련 정보를 검색하고 있습니다...",
            "progress_prefix": "🔍 진행률: ",
            "thinking": "🤔 추론 중...",
            "low_confidence_warning": "⚠️ *참고: 이 답변의 신뢰 점수가 낮습니다*",
            "support_msg": "더 자세한 정보를 제공해주시면 더 정확한 답변을 드릴 수 있습니다:",
            "error_msg": "😿 요청을 처리하는 중 오류가 발생했습니다.",
            "web_search_header": "### 웹 검색 결과",
            "web_search_no_results": "- 관련 웹 검색 결과가 없습니다."
        }
    }
}

# Select Active Personality with fallback to accounting
active_p = PERSONALITIES.get(BOT_PERSONALITY)
if not active_p:
    active_p = PERSONALITIES["accounting"]
    BOT_PERSONALITY = "accounting"

# Export Active Config
# PRIORITY: Personality Registry > .env Global Variables
ROLE = active_p["role"]
LANGUAGE = active_p["language"]
EMBED_PATH = active_p["embed_path"]
DATABASE = active_p["database"]
LOCAL_DATA = active_p["local_data"]
START_MESSAGE = active_p["start_message"]
UI = active_p["ui"]

# Diagnostic Log
logger.info(f"Loaded config from: {ENV_PATH}")
logger.info(f"Active Personality: {BOT_PERSONALITY}")
logger.info(f"Database Path: {DATABASE}")
logger.info(f"Embed Path: {EMBED_PATH}")

# Initialize tokenizer
TOKENIZER = None
if EMBED_PATH:
    try:
        TOKENIZER = AutoTokenizer.from_pretrained(EMBED_PATH)
    except Exception:
        pass