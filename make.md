# Reddit AI Scraper - Full Documentation

## Overview

AI-powered agent to scrape Reddit for software business opportunities using a multi-stage agentic pipeline.

## Architecture

The system follows the 4-stage pipeline from the original blueprint:

```
┌─────────────────────────────────────────────────────────────┐
│                    PAIN POINT RADAR                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   INGESTOR   │───▶│   FILTER     │───▶│   ANALYZER   │ │
│  │  (Scraper)   │    │  (Router)    │    │     (LLM)     │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│         │                   │                   │           │
│         ▼                   ▼                   ▼           │
│  Reddit JSON API     High Intent       OpenRouter AI        │
│  or Firecrawl       Keywords          (Gemini/Claude)       │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    DATABASE                           │   │
│  │  Notion / Slack / Discord / JSON                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Ingestor (Scraper)

Fetches posts from target subreddits using Reddit's free JSON API:

```python
url = f"https://www.reddit.com/r/{subreddit}/rising.json?limit=25"
```

Or use Firecrawl for enhanced scraping:
```bash
curl -X POST http://localhost:8080/firecrawl -d '{"url": "https://reddit.com/r/shopify/..."}'
```

### 2. Filter (Router)

Keyword-based filtering to discard 90% of noise:

**High Intent Keywords:**
- "is there a tool", "looking for a tool"
- "how do i automate", "tired of"
- "manually", "tedious", "repetitive"
- "using spreadsheet for", "workaround"

**Medium Intent:**
- "how do i", "help me", "struggling with"

### 3. Analyzer (LLM)

Uses OpenRouter API to extract structured insights:

**Prompt:**
```
Analyze this Reddit post and extract:
1. CORE_FRUSTRATION: What problem?
2. CURRENT_WORKAROUND: How they solve it now?
3. MONETIZATION_SCORE: 1-10 scale
4. SOFTWARE_OPPORTUNITY: What solution?
5. TARGET_USER: Who?
```

### 4. Output

Sends to:
- Notion database
- Slack webhook
- Discord webhook
- JSON/CSV files

## Target Subreddits

### Vertical Communities (Recommended)

| Category | Subreddits |
|----------|------------|
| E-commerce | shopify, shopifyapps, dropshipping |
| Business | smallbusiness, entrepreneur, startups, freelance |
| Productivity | notion, n8n, zapier, airtable |
| Tech | webdev, python, javascript, reactjs, aws |
| SaaS | saas, sideproject, indiehackers, bootstrapped |

## Installation

```bash
git clone https://github.com/dexter123233/reddit-ai-scraper.git
cd reddit-ai-scraper
python3 server.py
```

For LangGraph agent:
```bash
pip install langgraph langchain-openai
python3 langgraph_agent.py --subreddits shopify notion
```

## Usage

### Browser UI

Open http://localhost:8080

1. Select subreddits or use quick tags
2. Enable "AI Analysis" checkbox
3. Click "Scan + AI Analysis"
4. View results with extracted pain points

### Curl API

```bash
# Basic scan
curl -X POST http://localhost:8080/scan \
  -H "Content-Type: application/json" \
  -d '{"subreddits": ["shopify", "notion"]}'

# With AI analysis
curl -X POST http://localhost:8080/scan \
  -H "Content-Type: application/json" \
  -d '{"subreddits": ["shopify"], "ai_analyze": true}'

# Analyze specific posts
curl -X POST http://localhost:8080/analyze \
  -H "Content-Type: application/json" \
  -d '{"posts": [{"title": "...", "body": "..."}]}'
```

### LangGraph Agent

```bash
python3 langgraph_agent.py \
  --subreddits shopify notion smallbusiness \
  --openrouter-key sk-...
```

## Configuration

Set via UI or environment variables:

```bash
export OPENROUTER_API_KEY="sk-..."
export FIRECRAWL_API_KEY="fc-..."
export SLACK_WEBHOOK_URL="https://hooks.slack.com/..."
export NOTION_TOKEN="secret_..."
export NOTION_DB_ID="..."
```

## n8n Integration

1. Import `n8n-workflow.json` in n8n
2. Configure credentials:
   - Reddit API (optional)
   - OpenRouter API
   - Slack/Discord webhooks
   - Notion
3. Set schedule (e.g., every 4 hours)
4. Activate workflow

## Notion Database Setup

Create a database with these properties:

| Property | Type |
|----------|------|
| Name | Title |
| Subreddit | Text |
| URL | URL |
| Score | Number |
| Intent | Select (high/medium/low) |
| Problem | Text |
| Workaround | Text |
| Monetization | Number |
| Opportunity | Text |

## Pain Point Detection

The agent looks for these buy signals:

**Ultimate Buy Signals:**
- "Is there a tool for..."
- "Why isn't there..."
- "I wish there was..."

**Frustration Signals:**
- "Tired of..."
- "Sick of..."
- "Hate it when..."

**Inefficiency Signals:**
- "Manually..."
- "Tedious..."
- "Repetitive..."

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Browser UI |
| `/scan` | POST | Scan subreddits |
| `/analyze` | POST | AI analyze posts |
| `/config` | POST | Save config |
| `/list` | GET | List subreddits |
| `/results` | GET | Scan history |
| `/firecrawl` | POST | Firecrawl scrape |
| `/webhook/discord` | POST | Discord notification |
| `/webhook/slack` | POST | Slack notification |
| `/notion` | POST | Notion export |

## Troubleshooting

### No results
- Check subreddit names are correct
- Reddit may be rate limiting (wait and retry)

### AI analysis not working
- Verify OpenRouter API key is set
- Check API key has credits

### Webhooks not sending
- Verify webhook URLs are correct
- Check Notion database is shared with integration

## Files

| File | Description |
|------|-------------|
| `server.py` | Main HTTP server |
| `index.html` | Browser UI |
| `langgraph_agent.py` | LangGraph agent |
| `n8n-workflow.json` | n8n automation |
| `README.md` | Quick start |
| `make.md` | This file |
| `changelog.md` | Version history |
