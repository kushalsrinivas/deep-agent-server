from typing import Any, Dict, List

from .search import web_search, fetch_url


def get_social_followers(company: str) -> Dict[str, Any]:
    """Best-effort snapshot of Twitter/X and LinkedIn followers.

    We do not scrape behind logins; we rely on public profile pages or 3rd-party mentions.
    """
    sources: List[str] = []
    twitter = {"value": None, "source": None}
    linkedin = {"value": None, "source": None}

    # Twitter/X
    x_res = web_search(f"{company} official Twitter followers", max_results=5)
    if x_res.get("status") == "success":
        for r in x_res.get("data", []):
            href = r.get("href")
            if href and ("twitter.com" in href or "x.com" in href):
                sources.append(href)
                page = fetch_url(href)
                if page.get("status") == "success":
                    content = page.get("data", {}).get("content", "")
                    # Heuristic to find followers count mentions
                    for kw in ["Followers", "followers"]:
                        idx = content.find(kw)
                        if idx != -1:
                            window = content[max(0, idx - 50) : idx + 50]
                            twitter = {"value": window.strip(), "source": href}
                            break
                break

    # LinkedIn
    li_res = web_search(f"{company} LinkedIn followers", max_results=5)
    if li_res.get("status") == "success":
        for r in li_res.get("data", []):
            href = r.get("href")
            if href and "linkedin.com/company" in href:
                sources.append(href)
                # LinkedIn is often gated; we may not fetch meaningful content
                linkedin = {"value": None, "source": href}
                break

    return {
        "status": "success",
        "data": {
            "social": {
                "twitter_followers": twitter,
                "linkedin_followers": linkedin,
                "sources": list(dict.fromkeys(sources)),
            }
        },
    }


