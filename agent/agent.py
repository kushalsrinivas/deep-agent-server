from typing import Any, Dict
from google.adk.agents import Agent

# Import modular tools
from tools.search import web_search, news_search, fetch_url
from tools.profiles import (
    get_company_overview,
    get_company_leadership,
    get_company_competitors,
)
from tools.funding import get_company_funding_summary
from tools.traffic import get_web_traffic_summary
from tools.financials import detect_ticker, get_public_financials


root_agent = Agent(
    name="agent",
    model="gemini-2.0-flash",
    description="Company research agent that returns JSON-only structured reports from open-web sources.",
    instruction=
    """
    You are a company research agent. Always output a single JSON object only, no prose, no Markdown.

    Input: company name string, optionally a country for disambiguation.

    Process:
    - Detect the official website and a possible public stock ticker via detect_ticker.
    - Build an overview via get_company_overview.
    - Gather founders/leadership via get_company_leadership.
    - Identify key competitors via get_company_competitors.
    - Summarize funding from public sources via get_company_funding_summary.
    - Summarize web traffic signals via get_web_traffic_summary (approximate; cite sources).
    - Collect recent news via news_search.
    - If a ticker is found, optionally enrich with get_public_financials.

    Output schema (strict):
    {
      "company": {
        "name": string,
        "website": string | null,
        "sector": string | null,
        "industry": string | null,
        "hq": string | null,
        "founded_year": string | null,
        "type": string | null,
        "employees": string | null,
        "ticker": string | null,
        "market_cap": number | null,
        "annual_revenue": number | null,
        "linkedin_url": string | null,
        "twitter_url": string | null,
        "tagline": string | null
      },
      "founders_leadership": {
        "people": [ { "text": string, "source": string } ],
        "sources": [string]
      },
      "competitors": {
        "list": [ { "name": string, "note": string, "source": string } ],
        "sources": [string]
      },
      "funding": {
        "total_estimated_usd_millions": number | null,
        "last_round": { "headline_amount_usd_millions": number | null, "source": string | null } | null,
        "rounds": [ { "text": string, "source": string } ],
        "investors": [ { "text": string, "source": string } ],
        "sources": [string]
      },
      "web_traffic": {
        "summary": string,
        "trend_snippets": [string],
        "sources": [string]
      },
      "news": {
        "items": [ { "title": string, "url": string, "date": string | null, "source": string | null } ],
        "sources": [string]
      }
    }

    Rules:
    - JSON only. No additional text.
    - Include per-section sources arrays, deduplicated.
    - If data is uncertain or not found, set fields to null or leave arrays empty.
    """,
    tools=[
        # Discovery
        web_search,
        fetch_url,
        news_search,
        detect_ticker,
        # Profiles
        get_company_overview,
        get_company_leadership,
        get_company_competitors,
        # Funding / traffic / financials
        get_company_funding_summary,
        get_web_traffic_summary,
        get_public_financials,
    ],
)