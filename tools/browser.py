"""
JARVIS Tools - Browser Automation

Browser automation using Playwright with persistent context for session management.
Per user decision: visible window, persistent sessions, text extraction with highlighting.

Features:
- Navigate, extract, click, fill forms
- Screenshot capture
- Multi-tab management
- Multi-step research workflows with source citation
"""

import re
import time
from pathlib import Path
from typing import Any
from dataclasses import dataclass, field

from loguru import logger

from tools.base import BaseTool, ToolError, execute_with_error_handling


@dataclass
class SearchResult:
    """Represents a search result from the browser."""
    title: str
    url: str
    snippet: str


# Re-export from brain.research for convenience
try:
    from brain.research import ResearchResult, ResearchSource
except ImportError:
    @dataclass
    class ResearchResult:
        """Fallback ResearchResult if brain.research not available."""
        query: str
        sources: list = field(default_factory=list)
        summary: str = ""
        raw_extracts: list = field(default_factory=list)
    
    @dataclass
    class ResearchSource:
        """Fallback ResearchSource if brain.research not available."""
        title: str
        url: str
        content: str
        relevance_score: float = 0.0


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
    
    def click(self, selector: str, timeout: int = 5000) -> str:
        """Click an element on the page.
        
        Args:
            selector: CSS selector for the element to click
            timeout: Timeout in milliseconds
            
        Returns:
            Status message
        """
        if not self.page:
            raise ToolError("BrowserTool", "Browser not launched", "Call launch() first")
        
        try:
            self.page.click(selector, timeout=timeout)
            self.logger.info(f"Clicked element: {selector}")
            return f"Clicked: {selector}"
        except Exception as e:
            raise ToolError("BrowserTool", f"Click failed: {e}", f"Check selector: {selector}")
    
    def fill(self, selector: str, value: str, timeout: int = 5000) -> str:
        """Fill a form field with a value.
        
        Args:
            selector: CSS selector for the input field
            value: Value to fill in
            timeout: Timeout in milliseconds
            
        Returns:
            Status message
        """
        if not self.page:
            raise ToolError("BrowserTool", "Browser not launched", "Call launch() first")
        
        try:
            self.page.fill(selector, value, timeout=timeout)
            self.logger.info(f"Filled '{selector}' with '{value[:30]}...'")
            return f"Filled: {selector}"
        except Exception as e:
            raise ToolError("BrowserTool", f"Fill failed: {e}", f"Check selector: {selector}")
    
    def screenshot(self, path: str | None = None, full_page: bool = False) -> str:
        """Take a screenshot of the current page.
        
        Args:
            path: Optional path to save the screenshot
            full_page: If True, capture the full page
            
        Returns:
            Path to saved screenshot or status
        """
        if not self.page:
            raise ToolError("BrowserTool", "Browser not launched", "Call launch() first")
        
        if path is None:
            path = f"data/screenshots/screenshot_{int(time.time())}.png"
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        try:
            self.page.screenshot(path=path, full_page=full_page)
            self.logger.info(f"Screenshot saved: {path}")
            return f"Screenshot saved: {path}"
        except Exception as e:
            raise ToolError("BrowserTool", f"Screenshot failed: {e}")
    
    def get_tabs(self) -> list[dict[str, str]]:
        """Get all open tabs.
        
        Returns:
            List of tab info dicts with index, title, url
        """
        if not self.context:
            return []
        
        tabs = []
        for i, page in enumerate(self.context.pages):
            tabs.append({
                "index": i,
                "title": page.title() or "(loading)",
                "url": page.url or "about:blank",
            })
        return tabs
    
    def switch_tab(self, index: int) -> str:
        """Switch to a specific tab.
        
        Args:
            index: Tab index to switch to
            
        Returns:
            Status message
        """
        if not self.context:
            raise ToolError("BrowserTool", "Browser not launched")
        
        pages = self.context.pages
        if index < 0 or index >= len(pages):
            raise ToolError("BrowserTool", f"Invalid tab index: {index}", f"Available: 0-{len(pages)-1}")
        
        self.page = pages[index]
        self.page.bring_to_front()
        return f"Switched to tab {index}: {self.page.title()}"
    
    def new_tab(self, url: str | None = None) -> str:
        """Open a new tab.
        
        Args:
            url: Optional URL to navigate to
            
        Returns:
            Tab info
        """
        if not self.context:
            raise ToolError("BrowserTool", "Browser not launched")
        
        new_page = self.context.new_page()
        if url:
            new_page.goto(url, wait_until="domcontentloaded")
        self.page = new_page
        
        return f"New tab opened: {new_page.title() or url or 'about:blank'}"
    
    def wait_for(self, selector: str, timeout: int = 10000) -> str:
        """Wait for an element to appear on the page.
        
        Args:
            selector: CSS selector to wait for
            timeout: Timeout in milliseconds
            
        Returns:
            Status message
        """
        if not self.page:
            raise ToolError("BrowserTool", "Browser not launched")
        
        try:
            self.page.wait_for_selector(selector, timeout=timeout)
            return f"Element found: {selector}"
        except Exception as e:
            raise ToolError("BrowserTool", f"Timeout waiting for: {selector}")
    
    def press_key(self, key: str) -> str:
        """Press a keyboard key.
        
        Args:
            key: Key to press (e.g., 'Enter', 'Escape', 'Tab')
            
        Returns:
            Status message
        """
        if not self.page:
            raise ToolError("BrowserTool", "Browser not launched")
        
        self.page.keyboard.press(key)
        return f"Pressed: {key}"
    
    def scroll(self, direction: str = "down", amount: int = 500) -> str:
        """Scroll the page.
        
        Args:
            direction: 'up' or 'down'
            amount: Pixels to scroll
            
        Returns:
            Status message
        """
        if not self.page:
            raise ToolError("BrowserTool", "Browser not launched")
        
        delta = amount if direction == "down" else -amount
        self.page.mouse.wheel(0, delta)
        return f"Scrolled {direction} {amount}px"
    
    def get_url(self) -> str:
        """Get current page URL."""
        if not self.page:
            return "about:blank"
        return self.page.url
    
    def back(self) -> str:
        """Navigate back."""
        if not self.page:
            raise ToolError("BrowserTool", "Browser not launched")
        self.page.go_back()
        return f"Navigated back to: {self.page.url}"
    
    def forward(self) -> str:
        """Navigate forward."""
        if not self.page:
            raise ToolError("BrowserTool", "Browser not launched")
        self.page.go_forward()
        return f"Navigated forward to: {self.page.url}"
    
    def reload(self) -> str:
        """Reload the current page."""
        if not self.page:
            raise ToolError("BrowserTool", "Browser not launched")
        self.page.reload()
        return f"Reloaded: {self.page.title()}"
    
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
            
        Raises:
            ToolError: If URL is invalid
        """
        # URL validation with regex extraction
        import re
        url_pattern = re.compile(r'https?://[^\s]+|www\.[^\s]+')
        match = url_pattern.search(url)
        
        if not match:
            # Check if the input starts with www. and auto-prepend https://
            if url.strip().lower().startswith('www.'):
                url = 'https://' + url.strip()
                match = url_pattern.search(url)
            else:
                raise ToolError(
                    "BrowserTool",
                    "I need a URL to navigate to. Please provide one.",
                    "Provide a valid URL starting with http://, https://, or www."
                )
        
        # Extract validated URL
        validated_url = match.group(0)
        
        if not self.manager:
            self.launch()
        
        title = self.manager.navigate(validated_url)
        return f"Navigated to: {validated_url}\nPage title: {title}"
    
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
    
    def execute(self, action: str, **kwargs: Any) -> Any:
        """Execute a browser action.
        
        Args:
            action: Action to perform
            **kwargs: Arguments for the action
            
        Returns:
            Result of the action
        """
        actions = {
            "launch": self.launch,
            "navigate": lambda: self.navigate(kwargs.get("url", "")),
            "extract": lambda: self.extract(kwargs.get("selector")),
            "click": lambda: self.manager.click(kwargs["selector"], kwargs.get("timeout", 5000)) if self.manager else "No manager",
            "fill": lambda: self.manager.fill(kwargs["selector"], kwargs["value"], kwargs.get("timeout", 5000)) if self.manager else "No manager",
            "screenshot": lambda: self.manager.screenshot(kwargs.get("path"), kwargs.get("full_page", False)) if self.manager else "No manager",
            "tabs": lambda: self.manager.get_tabs() if self.manager else [],
            "switch_tab": lambda: self.manager.switch_tab(kwargs["index"]) if self.manager else "No manager",
            "new_tab": lambda: self.manager.new_tab(kwargs.get("url")) if self.manager else "No manager",
            "wait_for": lambda: self.manager.wait_for(kwargs["selector"], kwargs.get("timeout", 10000)) if self.manager else "No manager",
            "press_key": lambda: self.manager.press_key(kwargs["key"]) if self.manager else "No manager",
            "scroll": lambda: self.manager.scroll(kwargs.get("direction", "down"), kwargs.get("amount", 500)) if self.manager else "No manager",
            "get_url": lambda: self.manager.get_url() if self.manager else "about:blank",
            "back": lambda: self.manager.back() if self.manager else "No manager",
            "forward": lambda: self.manager.forward() if self.manager else "No manager",
            "reload": lambda: self.manager.reload() if self.manager else "No manager",
            "close": self.close,
        }
        
        if action not in actions:
            raise ToolError(
                "BrowserTool",
                f"Unknown action: {action}",
                f"Available: {', '.join(actions.keys())}"
            )
        
        return execute_with_error_handling(self.name, actions[action])
    
    def close(self) -> None:
        """Close the browser."""
        if self.manager:
            self.manager.close()
            self.manager = None


__all__ = ["BrowserTool", "BrowserManager", "SearchResult"]
