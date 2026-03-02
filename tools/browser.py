"""
JARVIS Tools - Browser Automation

Browser automation using Playwright with persistent context for session management.
Per user decision: visible window, persistent sessions, text extraction with highlighting.
"""

from pathlib import Path
from typing import Any
from dataclasses import dataclass

from loguru import logger

from tools.base import BaseTool, ToolError, execute_with_error_handling


@dataclass
class SearchResult:
    """Represents a search result from the browser."""
    title: str
    url: str
    snippet: str


class BrowserManager:
    """Manages Playwright browser instance with persistent context.
    
    Per user decision: headless=False for visible window, persistent context
    for session persistence.
    """
    
    def __init__(self, user_data_dir: str | None = None):
        """Initialize browser manager.
        
        Args:
            user_data_dir: Optional directory for persistent browser data (cookies, sessions)
        """
        self.user_data_dir = user_data_dir
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
        # Setup logging
        self.logger = logger.bind(component="BrowserManager")
    
    def launch(self) -> None:
        """Launch browser with Playwright.
        
        Raises:
            ToolError: If browser fails to launch
        """
        try:
            from playwright.sync_api import sync_playwright
            
            self.playwright = sync_playwright().start()
            
            # Use persistent context for session persistence (per user decision)
            if self.user_data_dir:
                self.context = self.playwright.chromium.launch_persistent_context(
                    self.user_data_dir,
                    headless=False,  # Visible window per user decision
                    viewport={"width": 1280, "height": 720},
                    ignore_default_args=["--enable-automation"],
                )
            else:
                self.browser = self.playwright.chromium.launch(
                    headless=False,  # Visible window per user decision
                    args=["--disable-blink-features=AutomationControlled"],
                )
                self.context = self.browser.new_context(
                    viewport={"width": 1280, "height": 720}
                )
            
            self.page = self.context.new_page()
            self.logger.info("Browser launched successfully with visible window")
            
        except ImportError as e:
            raise ToolError(
                "BrowserTool",
                "Playwright not installed",
                "Install with: pip install playwright && playwright install chromium"
            ) from e
        except Exception as e:
            raise ToolError(
                "BrowserTool",
                f"Failed to launch browser: {str(e)}",
                "Install browser: playwright install chromium"
            ) from e
    
    def navigate(self, url: str) -> str:
        """Navigate to a URL.
        
        Args:
            url: The URL to navigate to
            
        Returns:
            Page title
        """
        if not self.page:
            raise ToolError("BrowserTool", "Browser not launched", "Call launch() first")
        
        self.logger.info(f"Navigating to: {url}")
        response = self.page.goto(url, wait_until="domcontentloaded")
        
        if response and response.status >= 400:
            raise ToolError(
                "BrowserTool",
                f"HTTP error: {response.status}",
                f"Check if {url} is accessible"
            )
        
        return self.page.title()
    
    def extract(self, selector: str | None = None) -> str:
        """Extract content from the page.
        
        Args:
            selector: Optional CSS selector to extract specific element
            
        Returns:
            Extracted text content
        """
        if not self.page:
            raise ToolError("BrowserTool", "Browser not launched", "Call launch() first")
        
        if selector:
            # Extract specific element
            element = self.page.locator(selector)
            content = element.inner_text()
            self.logger.debug(f"Extracted content from selector: {selector}")
        else:
            # Extract entire page content
            content = self.page.content()
            self.logger.debug("Extracted entire page content")
        
        return content
    
    def search(self, query: str, num_results: int = 5) -> list[SearchResult]:
        """Search the web using DuckDuckGo.
        
        Args:
            query: The search query
            num_results: Number of results to return
            
        Returns:
            List of SearchResult objects
        """
        if not self.page:
            self.launch()
        
        # Navigate to DuckDuckGo
        self.navigate(f"https://duckduckgo.com/?q={query}&ia=web")
        
        # Wait for results to load
        self.page.wait_for_selector(".result__body", timeout=10000)
        
        results = []
        
        # Extract results
        result_elements = self.page.locator(".result__body").all()[:num_results]
        
        for element in result_elements:
            try:
                title_elem = element.locator(".result__title")
                url_elem = element.locator(".result__url")
                snippet_elem = element.locator(".result__snippet")
                
                title = title_elem.inner_text() if title_elem.count() > 0 else ""
                url = url_elem.inner_text() if url_elem.count() > 0 else ""
                snippet = snippet_elem.inner_text() if snippet_elem.count() > 0 else ""
                
                results.append(SearchResult(
                    title=title.strip(),
                    url=url.strip(),
                    snippet=snippet.strip()
                ))
            except Exception as e:
                self.logger.warning(f"Failed to extract result: {e}")
                continue
        
        self.logger.info(f"Found {len(results)} search results for query: {query}")
        return results
    
    def close(self) -> None:
        """Close the browser and cleanup."""
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            self.logger.info("Browser closed successfully")
        except Exception as e:
            self.logger.warning(f"Error closing browser: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        self.launch()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class BrowserTool(BaseTool):
    """Browser automation tool using Playwright.
    
    Per user decision:
    - headless=False (visible window)
    - Persistent sessions
    - Text extraction with highlighting
    """
    
    def __init__(self, user_data_dir: str | None = None):
        """Initialize browser tool.
        
        Args:
            user_data_dir: Optional directory for persistent browser data
        """
        super().__init__(name="BrowserTool")
        
        # Default user data dir in data directory
        if user_data_dir is None:
            data_dir = Path("data/browser")
            data_dir.mkdir(parents=True, exist_ok=True)
            user_data_dir = str(data_dir)
        
        self.user_data_dir = user_data_dir
        self.manager: BrowserManager | None = None
    
    def launch(self) -> str:
        """Launch the browser.
        
        Returns:
            Success message
        """
        self.manager = BrowserManager(user_data_dir=self.user_data_dir)
        self.manager.launch()
        return "Browser launched successfully with visible window"
    
    def navigate(self, url: str) -> str:
        """Navigate to a URL.
        
        Args:
            url: The URL to navigate to
            
        Returns:
            Page title
        """
        if not self.manager:
            self.launch()
        
        title = self.manager.navigate(url)
        return f"Navigated to: {url}\nPage title: {title}"
    
    def extract(self, selector: str | None = None) -> str:
        """Extract content from the current page.
        
        Args:
            selector: Optional CSS selector
            
        Returns:
            Extracted content
        """
        if not self.manager:
            raise ToolError("BrowserTool", "Browser not launched", "Call launch() or navigate() first")
        
        return self.manager.extract(selector)
    
    def search(self, query: str, num_results: int = 5) -> list[dict[str, str]]:
        """Search the web and return results.
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of {title, url, snippet} dicts
        """
        if not self.manager:
            self.launch()
        
        results = self.manager.search(query, num_results)
        
        # Return as dicts for easier serialization
        return [
            {
                "title": r.title,
                "url": r.url,
                "snippet": r.snippet
            }
            for r in results
        ]
    
    def execute(self, action: str, **kwargs: Any) -> Any:
        """Execute a browser action.
        
        Args:
            action: Action to perform (launch, navigate, extract, search)
            **kwargs: Arguments for the action
            
        Returns:
            Result of the action
        """
        actions = {
            "launch": self.launch,
            "navigate": lambda: self.navigate(kwargs.get("url", "")),
            "extract": lambda: self.extract(kwargs.get("selector")),
            "search": lambda: self.search(
                kwargs.get("query", ""),
                kwargs.get("num_results", 5)
            ),
        }
        
        if action not in actions:
            raise ToolError(
                "BrowserTool",
                f"Unknown action: {action}",
                f"Available actions: {', '.join(actions.keys())}"
            )
        
        return execute_with_error_handling(self.name, actions[action])
    
    def close(self) -> None:
        """Close the browser."""
        if self.manager:
            self.manager.close()
            self.manager = None
    
    def __del__(self):
        """Cleanup on deletion."""
        self.close()


__all__ = ["BrowserTool", "BrowserManager", "SearchResult"]
