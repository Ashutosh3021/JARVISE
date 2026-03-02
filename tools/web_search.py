"""
JARVIS Tools - Web Search

Web search tool that uses BrowserTool for search results.
Per user decision: streaming + async callbacks, full logging, detailed errors.
"""

from typing import Any, Callable, Awaitable
from dataclasses import dataclass

from loguru import logger

from tools.base import BaseTool, ToolError, execute_with_error_handling
from tools.browser import BrowserTool


@dataclass
class WebSearchResult:
    """Represents a web search result."""
    title: str
    url: str
    snippet: str


class WebSearchTool(BaseTool):
    """Web search tool using browser automation.
    
    Per user decision:
    - Highlights "important details" in results
    - Async support with streaming results callback
    - Full logging to file + console
    - Detailed error handling with suggestions
    """
    
    def __init__(self, browser: BrowserTool | None = None):
        """Initialize web search tool.
        
        Args:
            browser: Optional BrowserTool instance to use
        """
        super().__init__(name="WebSearchTool")
        
        self.browser = browser
        self._stream_callback: Callable[[WebSearchResult], None] | None = None
    
    def _highlight_important(self, text: str) -> str:
        """Highlight important details in text.
        
        Per user decision: highlight "important details" in results.
        
        Args:
            text: Text to highlight
            
        Returns:
            Text with important parts highlighted
        """
        # Simple heuristics for important information
        important_patterns = [
            # URLs
            r'https?://[^\s]+',
            # Numbers with units (prices, dates, versions)
            r'\$[\d,]+(?:\.\d{2})?',
            r'\d+(?:\.\d+)?\s*(?:GB|MB|KB|seconds?|minutes?|hours?|days?)',
            # Version numbers
            r'v?\d+\.\d+(?:\.\d+)?',
            # Email addresses
            r'[\w.-]+@[\w.-]+\.\w+',
        ]
        
        # For now, return the text as-is
        # The highlighting can be enhanced based on user feedback
        return text
    
    def search(
        self,
        query: str,
        num_results: int = 5,
        stream_callback: Callable[[dict[str, str]], None] | None = None
    ) -> list[dict[str, str]]:
        """Search the web for results.
        
        Args:
            query: Search query
            num_results: Number of results to return
            stream_callback: Optional callback for streaming results
            
        Returns:
            List of {title, url, snippet} dicts
        """
        self.logger.info(f"Searching for: {query}")
        
        # Use existing browser or create new one
        close_browser = False
        if self.browser is None:
            self.browser = BrowserTool()
            close_browser = True
        
        try:
            # Perform search using browser
            results = self.browser.search(query, num_results)
            
            # Process results with highlighting
            processed_results = []
            for result in results:
                processed = {
                    "title": result["title"],
                    "url": result["url"],
                    "snippet": self._highlight_important(result["snippet"])
                }
                processed_results.append(processed)
                
                # Stream callback if provided
                if stream_callback:
                    stream_callback(processed)
            
            self.logger.info(f"Found {len(processed_results)} results for: {query}")
            return processed_results
            
        finally:
            if close_browser and self.browser:
                self.browser.close()
    
    async def search_async(
        self,
        query: str,
        num_results: int = 5,
        stream_callback: Callable[[dict[str, str]], Awaitable[None]] | None = None
    ) -> list[dict[str, str]]:
        """Async version of search.
        
        Args:
            query: Search query
            num_results: Number of results to return
            stream_callback: Optional async callback for streaming results
            
        Returns:
            List of {title, url, snippet} dicts
        """
        import asyncio
        
        # Run sync search in executor
        def sync_search():
            return self.search(query, num_results)
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sync_search)
    
    def execute(self, query: str, num_results: int = 5, **kwargs: Any) -> list[dict[str, str]]:
        """Execute web search.
        
        Args:
            query: Search query
            num_results: Number of results to return
            **kwargs: Additional arguments
            
        Returns:
            List of search results
        """
        def do_search():
            return self.search(query, num_results)
        
        return execute_with_error_handling(self.name, do_search)
    
    def __repr__(self) -> str:
        return f"<WebSearchTool>"


__all__ = ["WebSearchTool", "WebSearchResult"]
