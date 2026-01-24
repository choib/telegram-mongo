import os
import pytest
from pathlib import Path
from dotenv import load_dotenv

# We import config specifically in each test or via fixture if needed
# but for basic environment checks we can look at os.environ

def test_env_file_exists():
    """Test 1: Check if .env file exists"""
    env_file = Path(".env")
    assert env_file.exists(), ".env file not found"

def test_gitignore_contains_env():
    """Test 2: Check if .gitignore exists and contains .env"""
    gitignore_file = Path(".gitignore")
    assert gitignore_file.exists(), ".gitignore not found"
    
    content = gitignore_file.read_text()
    assert '.env' in content, ".env not found in .gitignore"

def test_required_env_vars():
    """Test 3: Test environment variable presence (explicitly in .env or environment)"""
    # Note: We don't call load_dotenv here because pytest-dotenv or config.py might have already handled it
    # or we might be running in a CI environment where vars are already set.
    
    required_vars = [
        'TELEGRAM_BOT_TOKEN', 
        'OLLAMA_HOST', 
        'OLLAMA_MODEL', 
        # These below often have defaults in config.py, but we check if they are set
        # if the user intended to override them.
        'BOT_NAME', 
        'COLLECTION_NAME'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    assert not missing_vars, f"Missing required environment variables: {', '.join(missing_vars)}"

def test_config_loading():
    """Test 4: Verify that the config module loads and applies defaults correctly"""
    from config import config
    
    # Check that basic config objects are populated
    assert config.TELEGRAM_BOT_TOKEN is not None
    assert config.OLLAMA_MODEL is not None
    assert config.UI is not None
    assert isinstance(config.UI, dict)
    
    # Check defaults are applied if not in .env (these were failing the original script)
    assert config.EMBED_PATH is not None
    assert config.DATABASE is not None
    assert config.LOCAL_DATA is not None
    
    print(f"\n✓ Loaded Personality: {config.BOT_PERSONALITY}")
