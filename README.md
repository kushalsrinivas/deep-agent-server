# Company Research Agent (Google ADK)

A minimal AI agent built with Google ADK that performs deep company research from open-web sources and returns a JSON-only report. It uses DuckDuckGo search and light page fetching/parsing, plus optional yfinance enrichment if the company is public.

## Features

- Overview: website, industry, HQ, founding year, links (best-effort)
- Founders/Leadership: key names from public pages
- Competitors: related companies via public sources
- Funding summary: total and last-round signals from press/Wikipedia (approximate)
- Web traffic summary: public signals (e.g., Similarweb mentions) with citations (approximate)
- News: recent headlines via DuckDuckGo News
- Optional enrichment: detect ticker and fetch market cap/revenue via yfinance
- JSON-only output with per-section sources

## Requirements

- Python 3.10+
- ADK installed (verify: `adk --version`). If missing, follow ADK docs to install the CLI and Python package.
- Gemini API key for model access (Gemini Developer API):
  - `export GOOGLE_API_KEY="..."`

## Install

```bash
python -m venv venv
source venv/bin/activate
pip install -U yfinance pandas duckduckgo-search google-genai
# ADK should already be installed; if not, install per ADK docs
```

## Run (CORS-enabled FastAPI)

```bash
# Optional: allow your frontend origins (comma-separated)
export ALLOWED_ORIGINS="http://localhost:3000,https://yourapp.com"
# Optional: serve ADK web UI
export ADK_SERVE_WEB=true
# Optional: port/host
export PORT=8080
export HOST=0.0.0.0

python server.py
```

You should see the server listening on `http://localhost:8080`.

## Discover the app name

```bash
curl -s http://localhost:8080/list-apps
```

Expected to include `agent` as the app name (derived from the `agent/` folder).

## Create a session

```bash
curl -s -X POST \
  http://localhost:8080/apps/agent/users/demo/sessions/s1 \
  -H 'Content-Type: application/json' \
  -d '{"state":{}}'
```

## Ask the agent (non-streaming)

```bash
curl -s -X POST http://localhost:8080/run_sse \
  -H 'Content-Type: application/json' \
  -d '{
    "app_name": "agent",
    "user_id": "demo",
    "session_id": "s1",
    "new_message": {
      "role": "user",
      "parts": [{"text": "Tesla"}]
    },
    "streaming": false
  }'
```

## Input and output

- Input: company name string. Optionally include a country for disambiguation (e.g., "Acme Corp, country: USA").
- Output: a single JSON object only (no Markdown/prose) containing:
  - company overview, founders/leadership, competitors, funding summary, web traffic summary, news, and per-section sources.

## Tools available

- `web_search(query, max_results=5, region="wt-wt", safesearch="moderate", timelimit="")`
- `news_search(query, max_results=5, region="wt-wt", safesearch="moderate", timelimit="")`
- `fetch_url(url, max_chars=12000, timeout=12)`
- `detect_ticker(company, country="")`
- `get_company_overview(company, country="")`
- `get_company_leadership(company, country="", max_people=10)`
- `get_company_competitors(company, country="", max_competitors=10)`
- `get_company_funding_summary(company, country="", max_sources=6)`
- `get_web_traffic_summary(company, website="")`
- `get_public_financials(ticker)`

Notes:

- Use empty string for `timelimit` if no limit (or `d|w|m|y`).
- The agent model is `gemini-2.0-flash` (set `GOOGLE_API_KEY`).
- All data is best-effort from public sources; funding and traffic figures are approximate unless cited from authoritative sources.

## Alternate: ADK built-in API server (no custom CORS)

```bash
adk api_server
```

For strict CORS control, prefer `python server.py` which sets `allow_origins`.

## Project layout

```
  agent/
    __init__.py
    agent.py        # tools + root_agent
    tools/          # modular tools: search, profiles, funding, traffic, financials
server.py          # FastAPI app with CORS via get_fast_api_app
venv/              # local virtual env (optional)
```

## Troubleshooting

- Automatic function calling prefers simple parameter types; this repo keeps tool signatures simple (strings/ints, no unions).
- If CORS fails, confirm `ALLOWED_ORIGINS` and that you’re running `server.py` (not plain `adk api_server`).
- Ensure `GOOGLE_API_KEY` is set and valid for Gemini.
