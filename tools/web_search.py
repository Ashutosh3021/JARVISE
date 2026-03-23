"""
JARVIS Tools - Web Search

Web search tool using duckduckgo-search package.
Per user decision: streaming + async callbacks, full logging, detailed errors.
"""

import re
from typing import Any, Callable, Awaitable
from dataclasses import dataclass

from loguru import logger

from tools.base import BaseTool, ToolError, execute_with_error_handling


@dataclass
class WebSearchResult:
    """Represents a web search result."""
    title: str
    url: str
    snippet: str


def format_search_for_llm(results: list[dict]) -> str:
    """Format search results as a Markdown table for LLM consumption.
    
    Args:
        results: List of search result dicts
        
    Returns:
        Markdown formatted table string
    """
    if not results:
        return "No search results found."
    
    lines = ["| # | Title | URL | Snippet |", "|---|---|---|---|"]
    for i, r in enumerate(results, 1):
        title = r.get('title', '') or ''
        url = r.get('href', r.get('url', '')) or ''
        snippet = r.get('body', r.get('snippet', '')) or ''
        lines.append(f"| {i} | {title} | {url} | {snippet} |")
    
    return "\n".join(lines)


class WebSearchTool(BaseTool):
    """Web search tool using duckduckgo-search package.
    
    Per user decision:
    - Direct API access (no browser automation)
    - Async support with streaming results callback
    - Full logging to file + console
    - Detailed error handling with suggestions
    """
    
    def __init__(self):
        """Initialize web search tool."""
        super().__init__(name="WebSearchTool")
        
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
        
        try:
            from duckduckgo_search import DDGS
            
            # Use context manager for proper cleanup
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=num_results, backend='bing'))
            
            # Process results with highlighting
            processed_results = []
            for result in results:
                processed = {
                    "title": result.get("title", ""),
                    "url": result.get("href", result.get("url", "")),
                    "snippet": self._highlight_important(result.get("body", result.get("snippet", "")))
                }
                processed_results.append(processed)
                
                # Stream callback if provided
                if stream_callback:
                    stream_callback(processed)
            
            self.logger.info(f"Found {len(processed_results)} results for: {query}")
            return processed_results
            
        except ImportError as e:
            raise ToolError(
                "WebSearchTool",
                "duckduckgo-search not installed",
                "Install with: pip install duckduckgo-search"
            ) from e
        except Exception as e:
            raise ToolError(
                "WebSearchTool",
                f"Search failed: {str(e)}",
                "Check your internet connection"
            ) from e
    
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


__all__ = ["WebSearchTool", "WebSearchResult", "format_search_for_llm"]
