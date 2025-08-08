from typing import Any, Dict, List, Optional

from .search import web_search, fetch_url


def _result_url(results: List[Dict[str, Any]]) -> Optional[str]:
    for r in results:
        href = r.get("href") or r.get("url")
        if href:
            return href
    return None


def detect_official_website(company: str, country: str = "") -> Dict[str, Any]:
    """Attempt to detect the official website of a company using web search."""
    query = f"{company} official website"
    if country:
        query += f" {country}"
    res = web_search(query, max_results=5)
    if res.get("status") != "success":
        return res
    url = _result_url(res["data"]) if res.get("data") else None
    return {"status": "success", "data": {"website": url, "sources": [r.get("href") for r in res.get("data", []) if r.get("href")]}}


def get_company_overview(company: str, country: str = "") -> Dict[str, Any]:
    """Build a basic overview from public web sources (best-effort).

    Fields: name, website, sector, industry, hq, founded_year, type, employees, ticker,
            market_cap, revenue, linkedin_url, twitter_url, tagline
    """
    sources: List[str] = []
    overview: Dict[str, Any] = {"name": company}

    # 1) Official website
    site_res = detect_official_website(company, country)
    if site_res.get("status") == "success":
        overview["website"] = site_res.get("data", {}).get("website")
        sources.extend(site_res.get("data", {}).get("sources", []))

    # 2) Wikipedia page
    wiki_query = f"{company} wikipedia"
    if country:
        wiki_query += f" {country}"
    wiki_res = web_search(wiki_query, max_results=3)
    if wiki_res.get("status") == "success":
        wiki_url = None
        for r in wiki_res.get("data", []):
            href = r.get("href")
            if href and "wikipedia.org" in href:
                wiki_url = href
                break
        if wiki_url:
            sources.append(wiki_url)
            page = fetch_url(wiki_url)
            if page.get("status") == "success":
                content = page.get("data", {}).get("content", "")
                # Very light heuristics
                # Sector/Industry
                for key in ["Industry", "industry"]:
                    idx = content.lower().find("industry")
                    if idx != -1:
                        segment = content[idx: idx + 400]
                        overview.setdefault("industry", segment.split("\n")[0].split(":")[-1].strip())
                        break
                # Headquarters
                for label in ["Headquarters", "Headquarter", "Head office"]:
                    idx = content.lower().find(label.lower())
                    if idx != -1:
                        segment = content[idx: idx + 200]
                        overview.setdefault("hq", segment.split("\n")[0].split(":")[-1].strip())
                        break
                # Founded
                idx = content.lower().find("founded")
                if idx != -1:
                    segment = content[idx: idx + 200]
                    overview.setdefault("founded_year", segment.split("\n")[0].split(":")[-1].strip())

    # 3) LinkedIn page
    li_res = web_search(f"{company} LinkedIn company page", max_results=3)
    if li_res.get("status") == "success":
        for r in li_res.get("data", []):
            href = r.get("href") or ""
            if "linkedin.com/company" in href:
                overview["linkedin_url"] = href
                sources.append(href)
                break

    # 4) Twitter/X profile
    x_res = web_search(f"{company} Twitter official", max_results=3)
    if x_res.get("status") == "success":
        for r in x_res.get("data", []):
            href = r.get("href") or ""
            if "twitter.com" in href or "x.com" in href:
                overview["twitter_url"] = href
                sources.append(href)
                break

    return {"status": "success", "data": {"overview": overview, "sources": list(dict.fromkeys(sources))}}


def get_company_leadership(company: str, country: str = "", max_people: int = 10) -> Dict[str, Any]:
    """Identify founders and key decision makers using public sources."""
    sources: List[str] = []
    people: List[Dict[str, Any]] = []

    # Wikipedia often lists founders and key people
    wiki_query = f"{company} founders site:wikipedia.org"
    if country:
        wiki_query += f" {country}"
    wiki_res = web_search(wiki_query, max_results=5)
    if wiki_res.get("status") == "success":
        for r in wiki_res.get("data", []):
            href = r.get("href")
            if href and "wikipedia.org" in href:
                sources.append(href)
                page = fetch_url(href)
                if page.get("status") == "success":
                    content = page.get("data", {}).get("content", "")
                    # Basic heuristics to find names around keywords
                    for kw in ["Founded by", "Founder", "Founders", "Key people", "Chief Executive Officer", "CEO", "CFO", "CTO"]:
                        idx = 0
                        while True:
                            p = content.find(kw)
                            if p == -1:
                                break
                            segment = content[p : p + 400]
                            # Extract candidate names (very naive split)
                            lines = [ln for ln in segment.split("\n") if ln.strip()]
                            for ln in lines:
                                if any(t in ln for t in ["CEO", "CFO", "CTO", "Founder", "founder", "Chief", "President", "Chairman", "Chairwoman"]):
                                    if len(people) < max_people:
                                        people.append({"text": ln.strip(), "source": href})
                            content = content[p + len(kw) :]

    # Company website leadership page if present
    site_res = detect_official_website(company, country)
    site = site_res.get("data", {}).get("website") if site_res.get("status") == "success" else None
    if site:
        about_res = web_search(f"site:{site} leadership OR team OR management OR founders", max_results=5)
        if about_res.get("status") == "success":
            for r in about_res.get("data", []):
                href = r.get("href")
                if href and href.startswith("http"):
                    sources.append(href)
                    page = fetch_url(href)
                    if page.get("status") == "success":
                        content = page.get("data", {}).get("content", "")
                        lines = [ln for ln in content.split("\n") if ln.strip()]
                        for ln in lines:
                            if any(
                                t in ln
                                for t in [
                                    "CEO",
                                    "CFO",
                                    "CTO",
                                    "COO",
                                    "Chief",
                                    "Founder",
                                    "founder",
                                    "VP",
                                    "Vice President",
                                    "President",
                                    "Head of",
                                ]
                            ):
                                if len(people) < max_people:
                                    people.append({"text": ln.strip(), "source": href})

    return {"status": "success", "data": {"people": people, "sources": list(dict.fromkeys(sources))}}


def get_company_competitors(company: str, country: str = "", max_competitors: int = 10) -> Dict[str, Any]:
    """Find competitors from public sources (best-effort)."""
    sources: List[str] = []
    competitors: List[Dict[str, Any]] = []

    queries = [
        f"{company} competitors",
        f"{company} alternatives",
        f"{company} similar companies",
    ]
    if country:
        queries = [q + f" {country}" for q in queries]

    for q in queries:
        res = web_search(q, max_results=10)
        if res.get("status") == "success":
            for r in res.get("data", []):
                href = r.get("href")
                if href:
                    sources.append(href)
                title = r.get("title") or ""
                snippet = r.get("snippet") or ""
                name = title.split(" vs ")[0].split("Competitors")[0].strip(" -|:")
                if name and len(competitors) < max_competitors:
                    competitors.append({"name": name, "note": snippet[:200], "source": href})

    # Deduplicate by name
    seen = set()
    deduped: List[Dict[str, Any]] = []
    for c in competitors:
        if c["name"].lower() in seen:
            continue
        seen.add(c["name"].lower())
        deduped.append(c)

    return {"status": "success", "data": {"competitors": deduped, "sources": list(dict.fromkeys(sources))}}


