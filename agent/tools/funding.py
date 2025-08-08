from typing import Any, Dict, List

from .search import web_search, fetch_url


def get_company_funding_summary(company: str, country: str = "", max_sources: int = 6) -> Dict[str, Any]:
    """Best-effort funding summary using public sources (press releases, news, Wikipedia).

    Returns total (if confidently extracted), last round snapshot, list of notable investors, and sources.
    """
    queries = [
        f"{company} funding rounds",
        f"{company} total funding",
        f"{company} investors",
        f"{company} latest funding",
        f"{company} raises",
        f"{company} series funding",
    ]
    if country:
        queries = [q + f" {country}" for q in queries]

    sources: List[str] = []
    rounds: List[Dict[str, Any]] = []
    investors: List[Dict[str, Any]] = []
    total_amount = None
    last_round: Dict[str, Any] | None = None

    for q in queries:
        res = web_search(q, max_results=5)
        if res.get("status") != "success":
            continue
        for r in res.get("data", [])[:max_sources]:
            href = r.get("href")
            if not href:
                continue
            sources.append(href)
            page = fetch_url(href)
            if page.get("status") != "success":
                continue
            content = (page.get("data", {}) or {}).get("content", "")
            # Naive pattern extraction
            for marker in ["Series", "Seed", "Pre-Seed", "Angel", "Round", "IPO", "Grant"]:
                if marker.lower() in content.lower():
                    rounds.append({"text": content[:800], "source": href})
                    break
            # Investors
            if "investor" in content.lower() or "led by" in content.lower():
                investors.append({"text": content[:400], "source": href})  # type: ignore[arg-type]

            # Try to capture amounts by simple $/€/£ pattern
            import re

            amt_matches = re.findall(r"\$\s?([0-9.,]+)\s?(million|billion|m|bn|b)?", content, flags=re.I)
            if amt_matches:
                # Keep the largest match as a proxy for total/round headline
                def normalize(val: tuple[str, str | None]) -> float:
                    num, unit = val
                    n = float(num.replace(",", ""))
                    unit = (unit or "").lower()
                    if unit in ("billion", "bn", "b"):
                        n *= 1_000
                    return n

                largest = max(amt_matches, key=normalize)
                normalized = normalize(largest)
                if (total_amount or 0) < normalized:
                    total_amount = normalized
                    last_round = {"headline_amount_usd_millions": normalized, "source": href}

    # Build output
    return {
        "status": "success",
        "data": {
            "funding": {
                "total_estimated_usd_millions": total_amount,
                "last_round": last_round,
                "rounds": rounds,
                "investors": investors,
                "sources": list(dict.fromkeys(sources)),
            }
        },
    }


