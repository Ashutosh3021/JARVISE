"""
JARVIS Brain Layer - Browser Research Workflow

Multi-step research automation:
1. Search a query
2. Open top results
3. Extract content from each
4. Compile sources with citations
"""

import re
from dataclasses import dataclass, field
from typing import Any

from loguru import logger


@dataclass
class ResearchSource:
    """A single research source."""
    title: str
    url: str
    content: str
    relevance_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "content": self.content[:500],
            "relevance_score": self.relevance_score,
        }


@dataclass
class ResearchResult:
    """Aggregated research result."""
    query: str
    sources: list[ResearchSource] = field(default_factory=list)
    combined_text: str = ""
    source_count: int = 0

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "source_count": self.source_count,
            "sources": [s.to_dict() for s in self.sources],
        }

    def format_citations(self) -> str:
        """Format sources as numbered citations."""
        if not self.sources:
            return "No sources found."
        lines = ["## Sources\n"]
        for i, src in enumerate(self.sources, 1):
            lines.append(f"[{i}] {src.title}")
            lines.append(f"    {src.url}\n")
        return "\n".join(lines)

    def format_with_citations(self) -> str:
        """Format combined text with inline citations."""
        parts = []
        if self.combined_text:
            parts.append(self.combined_text)
        parts.append("")
        parts.append(self.format_citations())
        return "\n".join(parts)


class ResearchWorkflow:
    """
    Multi-step research workflow using the browser.

    Steps:
    1. Navigate to search engine
    2. Enter query and search
    3. Extract search result links
    4. Visit top N results
    5. Extract content from each page
    6. Compile with citations
    """

    DEFAULT搜索引擎 = "https://www.google.com"
    MAX_SOURCES = 5

    def __init__(self, browser_tool: Any = None):
        """
        Args:
            browser_tool: BrowserTool instance (creates lazy if None)
        """
        self._browser_tool = browser_tool

    @property
    def browser(self):
        if self._browser_tool is None:
            from tools.browser import BrowserTool
            self._browser_tool = BrowserTool()
        return self._browser_tool

    def research(
        self,
        query: str,
        max_sources: int = 3,
        engine: str = "google",
    ) -> ResearchResult:
        """
        Execute a full research workflow.

        Args:
            query: Research query
            max_sources: Maximum sources to visit
            engine: Search engine ("google" or "duckduckgo")

        Returns:
            ResearchResult with sources and combined text
        """
        result = ResearchResult(query=query)

        try:
            # Step 1: Search
            search_urls = {
                "google": f"https://www.google.com/search?q={query.replace(' ', '+')}",
                "duckduckgo": f"https://duckduckgo.com/?q={query.replace(' ', '+')}",
            }
            url = search_urls.get(engine, search_urls["google"])

            self.browser.execute(action="navigate", url=url)
            logger.info(f"Research: searched '{query}' on {engine}")

            # Step 2: Extract search result links
            links = self._extract_search_results()
            logger.info(f"Found {len(links)} search results")

            # Step 3: Visit top results and extract content
            visited = 0
            for link in links[:max_sources]:
                if visited >= max_sources:
                    break

                try:
                    self.browser.execute(action="navigate", url=link["url"])
                    content = self.browser.execute(action="extract")

                    # Clean and truncate content
                    content = self._clean_content(content)
                    if len(content) > 50:
                        source = ResearchSource(
                            title=link.get("title", "Untitled"),
                            url=link["url"],
                            content=content[:2000],
                        )
                        result.sources.append(source)
                        visited += 1
                        logger.info(f"Extracted: {link['url'][:60]}...")
                except Exception as e:
                    logger.warning(f"Failed to extract {link['url']}: {e}")
                    continue

            result.source_count = len(result.sources)
            result.combined_text = self._combine_texts(result.sources)

        except Exception as e:
            logger.error(f"Research workflow failed: {e}")
            result.combined_text = f"Research error: {e}"

        return result

    def quick_research(self, query: str, engine: str = "duckduckgo") -> str:
        """
        Quick single-page research: search and extract the first result.

        Args:
            query: Search query
            engine: Search engine to use

        Returns:
            Extracted text from first result with citation
        """
        result = self.research(query, max_sources=1, engine=engine)
        if result.sources:
            return f"{result.sources[0].content}\n\nSource: [{result.sources[0].title}]({result.sources[0].url})"
        return "No results found."

    def _extract_search_results(self) -> list[dict[str, str]]:
        """Extract search result links from the current search page."""
        try:
            content = self.browser.execute(action="extract")
            return self._parse_search_results(content)
        except Exception:
            return []

    def _parse_search_results(self, html: str) -> list[dict[str, str]]:
        """Parse search result links from HTML content."""
        results = []
        seen_urls = set()

        # Find all links in the content
        url_pattern = re.compile(
            r'https?://[^\s"\'<>]+', re.IGNORECASE
        )

        # Simple extraction: find URLs and nearby text
        lines = html.split("\n")
        for line in lines:
            urls = url_pattern.findall(line)
            for url in urls:
                # Skip search engine internal links
                if any(skip in url for skip in [
                    "google.com", "duckduckgo.com", "bing.com",
                    "youtube.com/results", "google.com/search",
                    "javascript:", "#", ".png", ".jpg", ".gif",
                ]):
                    continue

                if url not in seen_urls:
                    seen_urls.add(url)
                    results.append({
                        "title": line[:100].strip(),
                        "url": url,
                    })

        return results[:10]

    def _clean_content(self, content: str) -> str:
        """Clean extracted content for readability."""
        # Remove script/style tags
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
        # Remove HTML tags
        content = re.sub(r'<[^>]+>', ' ', content)
        # Collapse whitespace
        content = re.sub(r'\s+', ' ', content).strip()
        return content

    def _combine_texts(self, sources: list[ResearchSource]) -> str:
        """Combine text from multiple sources."""
        parts = []
        for i, src in enumerate(sources, 1):
            parts.append(f"--- Source {i}: {src.title} ---")
            parts.append(src.content[:1000])
            parts.append("")
        return "\n".join(parts)


__all__ = ["ResearchWorkflow", "ResearchResult", "ResearchSource"]
