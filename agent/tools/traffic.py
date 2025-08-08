from typing import Any, Dict, List

from .search import web_search, fetch_url


def get_web_traffic_summary(company: str, website: str = "") -> Dict[str, Any]:
    """Best-effort web traffic summary using public mentions (Similarweb, press, blog posts).

    Returns a summary string, any trend snippets discovered, and source URLs.
    """
    queries: List[str] = []
    if website:
        queries.append(f"site:similarweb.com {website}")
        queries.append(f"{company} traffic Similarweb")
    else:
        queries.append(f"{company} website traffic")
        queries.append(f"{company} monthly visits Similarweb")
    queries.append(f"{company} web traffic trend")

    sources: List[str] = []
    trend_snippets: List[str] = []

    for q in queries:
        res = web_search(q, max_results=5)
        if res.get("status") != "success":
            continue
        for r in res.get("data", []):
            href = r.get("href")
            if href:
                sources.append(href)
                page = fetch_url(href)
                if page.get("status") == "success":
                    content = page.get("data", {}).get("content", "")
                    # Extract small snippet windows mentioning visits/traffic
                    lower = content.lower()
                    for kw in ["visits", "monthly visits", "traffic", "unique visitors"]:
                        idx = lower.find(kw)
                        if idx != -1:
                            snippet = content[max(0, idx - 120) : idx + 180]
                            trend_snippets.append(snippet.strip())

    summary = "Public sources indicate recent traffic signals; figures are approximate and may be outdated."
    return {
        "status": "success",
        "data": {
            "web_traffic": {
                "summary": summary,
                "trend_snippets": trend_snippets[:10],
                "sources": list(dict.fromkeys(sources)),
            }
        },
    }


