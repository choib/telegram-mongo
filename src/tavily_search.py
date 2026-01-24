"""
Tavily search integration for web search results.
"""
import logging
from typing import List, Dict, Any
from langchain_community.tools.tavily_search import TavilySearchResults

from config import config

logger = logging.getLogger(__name__)


class TavilyWebSearch:
    """Wrapper for Tavily search API to get web search results."""
    
    def __init__(self, api_key: str = None, max_results: int = 3):
        """
        Initialize Tavily search client.
        
        Args:
            api_key: Tavily API key. If None, will try to get from environment.
            max_results: Maximum number of search results to return.
        """
        self.api_key = api_key
        self.max_results = max_results
        self.client = None
        self._initialized = False
    
    async def initialize(self):
        """Lazy initialization of the Tavily client."""
        if not self._initialized and self.client is None:
            try:
                self.client = TavilySearchResults(
                    tavily_api_key=self.api_key,
                    max_results=self.max_results
                )
                self._initialized = True
                logger.info("Tavily search client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Tavily client: {e}")
                self.client = None
                self._initialized = False
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search the web using Tavily and return results.
        
        Args:
            query: Search query
            
        Returns:
            List of search results with metadata
            
        Raises:
            RuntimeError: If Tavily client is not initialized
        """
        # Lazy initialization
        if not self._initialized:
            await self.initialize()
        
        if self.client is None:
            raise RuntimeError("Tavily client not initialized")
        
        try:
            logger.info(f"Searching Tavily for: '{query}'")
            results = await self.client.arun(query)
            logger.info(f"Found {len(results)} Tavily search results")
            
            # Log detailed information about each result
            for i, result in enumerate(results, 1):
                logger.info(f"  Result {i}: {result.get('title', 'No title')} - {result.get('url', 'No URL')}")
            
            return results
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return []
    
    async def get_search_summary(self, query: str) -> str:
        """
        Get a summary of web search results for a query.
        
        Args:
            query: Search query
            
        Returns:
            Formatted string with search results summary
        """
        results = await self.search(query)
        
        if not results:
            logger.info("No Tavily search results found")
            return f"""{config.UI['web_search_header']}
{config.UI['web_search_no_results']}"""
        
        # Check if results is a string (old API format) or list of dicts (new format)
        if isinstance(results, str):
            # Old API format - return the string directly
            logger.info(f"Tavily search results (string format): {results[:200]}...")
            return f"""{config.UI['web_search_header']}
{results}"""
        
        # New API format - list of dictionaries
        summary_lines = [config.UI['web_search_header']]
        for i, result in enumerate(results, 1):
            url = result.get('url', 'Unknown URL')
            title = result.get('title', 'Untitled')
            content = result.get('content', '')[:200] + '...' if len(result.get('content', '')) > 200 else result.get('content', '')
            
            summary_lines.append(f"\n{i}. [{title}]({url})")
            summary_lines.append(f"   {content}")
            
            # Log each result
            logger.info(f"Tavily result {i}: Title='{title}', URL='{url}', Content length={len(result.get('content', ''))}")
        
        logger.info(f"Tavily search completed. Total results: {len(results)}")
        return "\n".join(summary_lines)
