from typing import Any, Dict, List

from .search import web_search


def detect_ticker(company: str, country: str = "") -> Dict[str, Any]:
    """Attempt to detect a public ticker for the company via web search."""
    q = f"{company} stock ticker"
    if country:
        q += f" {country}"
    res = web_search(q, max_results=5)
    if res.get("status") != "success":
        return res
    ticker = None
    sources: List[str] = []
    for r in res.get("data", []):
        href = r.get("href") or ""
        if any(s in href for s in ["finance.yahoo.com", "nasdaq.com", "bloomberg.com", "google.com/finance", "reuters.com"]):
            sources.append(href)
            # Heuristic: look for patterns like (NASDAQ: TSLA)
            title = (r.get("title") or "") + " " + (r.get("snippet") or "")
            import re
            m = re.search(r"\(([A-Z]+:[A-Z.]+)\)", title)
            if m:
                ticker = m.group(1).split(":")[-1]
                break
            # fallback: search for uppercase token likely ticker
            tokens = [t.strip().upper() for t in title.replace("-", " ").split() if t.isalpha() and len(t) <= 5]
            for t in tokens:
                if len(t) >= 3:
                    ticker = t
                    break
        if ticker:
            break
    return {"status": "success", "data": {"ticker": ticker, "sources": sources}}


def get_public_financials(ticker: str) -> Dict[str, Any]:
    """Retrieve public market snapshot using yfinance if available."""
    try:
        import yfinance as yf

        t = yf.Ticker(ticker)
        info = {}
        # fast_info when available
        fi = getattr(t, "fast_info", None)
        if fi is not None:
            info["market_cap"] = getattr(fi, "market_cap", None)
            info["currency"] = getattr(fi, "currency", None)
        # try to fetch revenue from financials
        try:
            fin = t.financials
            if fin is not None and not fin.empty:
                if "Total Revenue" in fin.index:
                    info["annual_revenue"] = float(fin.loc["Total Revenue"].iloc[0])
        except Exception:  # noqa: BLE001
            pass

        return {"status": "success", "data": {"financials": info}}
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "error_message": f"Failed to fetch financials for {ticker}: {e}"}


