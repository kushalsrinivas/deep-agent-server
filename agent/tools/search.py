from typing import Any, Dict, List

from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup


def web_search(
    query: str,
    max_results: int = 5,
    region: str = "wt-wt",
    safesearch: str = "moderate",
    timelimit: str = "",
) -> Dict[str, Any]:
    """General web search via DuckDuckGo.

    Returns a list of results with title, href, snippet, and source.
    """
    try:
        results: List[Dict[str, Any]] = []
        with DDGS() as ddgs:
            tl = None if not timelimit else timelimit
            for r in ddgs.text(
                query,
                region=region,
                safesearch=safesearch,
                timelimit=tl,
                max_results=max_results,
            ):
                results.append(
                    {
                        "title": r.get("title"),
                        "href": r.get("href"),
                        "snippet": r.get("body"),
                        "source": r.get("source"),
                    }
                )
        return {"status": "success", "data": results}
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "error_message": f"Search failed: {e}"}


def news_search(
    query: str,
    max_results: int = 5,
    region: str = "wt-wt",
    safesearch: str = "moderate",
    timelimit: str = "",
) -> Dict[str, Any]:
    """News-focused search via DuckDuckGo.

    Returns a list of news items with title, url, date, and source.
    """
    try:
        results: List[Dict[str, Any]] = []
        with DDGS() as ddgs:
            tl = None if not timelimit else timelimit
            for r in ddgs.news(
                query,
                region=region,
                safesearch=safesearch,
                timelimit=tl,
                max_results=max_results,
            ):
                # duckduckgo_search news keys: title, date, source, url
                results.append(
                    {
                        "title": r.get("title"),
                        "url": r.get("url") or r.get("href"),
                        "date": r.get("date"),
                        "source": r.get("source"),
                    }
                )
        return {"status": "success", "data": results}
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "error_message": f"News search failed: {e}"}


def fetch_url(url: str, max_chars: int = 12000, timeout: int = 12) -> Dict[str, Any]:
    """Fetch and extract readable text content from a URL.

    - Truncates content to max_chars
    - Returns page title when available
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()

        content_type = (resp.headers.get("content-type") or "").lower()
        text = resp.text

        # Heuristic: treat as HTML if header says so or content looks like HTML
        is_html = "text/html" in content_type or "<html" in text[:200].lower()

        if is_html:
            soup = BeautifulSoup(text, "lxml")
            for tag in soup(["script", "style", "noscript", "svg", "canvas"]):
                tag.decompose()
            title = None
            if soup.title and soup.title.string:
                title = soup.title.string.strip()
            raw_text = soup.get_text(separator="\n")
            lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
            joined = "\n".join(lines)
            content = joined[:max_chars]
            return {"status": "success", "data": {"url": url, "title": title, "content": content}}
        # Non-HTML: return as text
        return {"status": "success", "data": {"url": url, "title": None, "content": text[:max_chars]}}
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "error_message": f"Failed to fetch {url}: {e}"}


