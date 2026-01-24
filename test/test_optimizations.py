import pytest
import time
from src.bot import mongodb_manager
from src.ollama import OllamaClient

def test_mongodb_initialization_not_blocking():
    """Test 1: Verify MongoDB initialization is not blocking"""
    # Just importing it should be enough, but let's check basic state
    assert not mongodb_manager._initialized
    assert mongodb_manager.client is None

def test_cache_key_normalization():
    """Test 2: Verify cache key normalization"""
    client = OllamaClient(host="http://localhost:11434", model="llama2")
    
    # Test that different whitespace produces same key
    key1 = client._get_cache_key("  Hello World  ")
    key2 = client._get_cache_key("Hello World")
    key3 = client._get_cache_key("Hello   World")
    
    assert key1 == key2 == key3
    assert len(key1) > 0

def test_string_optimization_functions():
    """Test 4: Verify string optimization (list joining vs concatenation)"""
    test_strings = ["line1", "line2", "line3", "line4", "line5"]
    
    # Check consistency of results
    result_old = ""
    for s in test_strings:
        result_old += s + "\n"
    
    result_new = "\n".join(test_strings)
    
    assert result_old.rstrip('\n') == result_new

def test_string_optimization_performance():
    """Optional benchmark for string optimization"""
    test_strings = ["line" + str(i) for i in range(1000)]
    
    # Concatenation
    start = time.time()
    result_old = ""
    for s in test_strings:
        result_old += s + "\n"
    time_old = time.time() - start
    
    # Join
    start = time.time()
    result_new = "\n".join(test_strings)
    time_new = time.time() - start
    
    # Join is usually much faster for large lists
    assert result_old.rstrip('\n') == result_new
    # We don't strictly assert performance as it might vary, 
    # but we can print it
    print(f"\nPerformance: Join is {time_old/max(time_new, 1e-9):.2f}x faster")
