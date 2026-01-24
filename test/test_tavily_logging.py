# Test Script for Tavily Search Logging

"""
This script demonstrates the enhanced logging functionality for Tavily search results.
It shows what logs will be generated when web search is performed.
"""

import logging
from src.tavily_search import TavilyWebSearch

# Configure logging to show the enhanced output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_tavily_logging():
    """
    Test the enhanced logging in TavilyWebSearch class.
    
    This demonstrates:
    1. Search query logging
    2. Results count logging
    3. Individual result logging (title, URL, content length)
    4. Summary logging
    """
    print("=" * 80)
    print("TAVILY SEARCH LOGGING DEMONSTRATION")
    print("=" * 80)
    
    # Create a TavilyWebSearch instance
    # Note: This won't actually connect without a valid API key
    web_search = TavilyWebSearch(api_key=None, max_results=3)
    
    print("\n1. Testing search() method logging:")
    print("-" * 80)
    print("When a search is performed, the following logs are generated:")
    print("  - INFO: Searching Tavily for: '<query>'")
    print("  - INFO: Found <N> Tavily search results")
    print("  - INFO:   Result 1: <title> - <url>")
    print("  - INFO:   Result 2: <title> - <url>")
    print("  - ...")
    
    print("\n2. Testing get_search_summary() method logging:")
    print("-" * 80)
    print("When generating a summary, the following logs are generated:")
    print("  - INFO: No Tavily search results found (if no results)")
    print("  - INFO: Tavily search results (string format): '<first 200 chars>' (if string format)")
    print("  - INFO: Tavily result 1: Title='<title>', URL='<url>', Content length=<N>")
    print("  - INFO: Tavily result 2: Title='<title>', URL='<url>', Content length=<N>")
    print("  - ...")
    print("  - INFO: Tavily search completed. Total results: <N>")
    
    print("\n3. Testing bot.py logging:")
    print("-" * 80)
    print("When web search results are included in the LLM payload:")
    print("  - INFO: Web search results included in payload. Length: <N> characters")
    print("  - INFO: Generated payload for LLM. Total length: <N> characters")
    
    print("\n" + "=" * 80)
    print("BENEFITS OF ENHANCED LOGGING")
    print("=" * 80)
    print("""
1. Debugging: Easily identify which queries are being searched
2. Monitoring: Track search result quality and relevance
3. Performance: Monitor payload sizes for optimization
4. Error Tracking: Quickly identify search failures
5. Analytics: Understand user query patterns

Example real-world scenario:
- User asks: "What is the maximum working hours in Korea?"
- Logs show: Search query, found results, which URLs were used
- If no results: "No Tavily search results found" helps identify the issue
- If results are too long: Can optimize content length
""")
    
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_tavily_logging()
