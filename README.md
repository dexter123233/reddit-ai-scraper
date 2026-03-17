# Reddit AI Scraper - Pain Point Radar

AI-powered agent to scrape Reddit for software business opportunities.

## Quick Start

```bash
python3 server.py
```

Then open http://localhost:8080

## Features

- 🧠 **AI Pain Point Analysis** - Extracts problem, workaround, monetization score
- 🔥 **Multi-stage Pipeline** - Ingest → Filter → Analyze → Output
- 🌐 **Browser UI** - Full GUI with dark theme
- 🔍 **Intent Detection** - High/medium intent keyword filtering
- 📊 **Integrations** - Discord, Slack, Notion, CSV/JSON
- 🤖 **LangGraph Agent** - Agentic workflow with reasoning
- 🔗 **Firecrawl Ready** - Enhanced scraping capability
- ⏱️ **n8n Workflow** - Visual automation

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    REDDIT PAIN POINT RADAR                   │
├─────────────────────────────────────────────────────────────┤
│  Stage 1: Ingestor     →  Fetch posts from Reddit          │
│  Stage 2: Filter/Router →  Keyword-based intent detection   │
│  Stage 3: Analyzer      →  LLM pain point extraction        │
│  Stage 4: Output       →  Notion/Slack/Discord             │
└─────────────────────────────────────────────────────────────┘
```

## AI Analysis

When enabled, the AI extracts:

- **Core Frustration** - The problem being described
- **Current Workaround** - How they're solving it now (e.g., "messy spreadsheet")
- **Monetization Score** - 1-10 scale of opportunity
- **Software Opportunity** - What type of solution needed
- **Target User** - Who experiences this problem

## Usage

### Browser UI

1. Open http://localhost:8080
2. Enter subreddits or use quick tags
3. Check "Enable AI Analysis"
4. Click Scan
5. View results with AI analysis

### CLI

```bash
# Basic scan
python3 server.py

# LangGraph agent (requires pip install langgraph langchain-openai)
python3 langgraph_agent.py --subreddits shopify notion smallbusiness
```

### Curl Commands

```bash
# Scan with AI
curl -X POST http://localhost:8080/scan \
  -H "Content-Type: application/json" \
  -d '{"subreddits": ["shopify", "notion"], "ai_analyze": true}'

# Analyze specific posts
curl -X POST http://localhost:8080/analyze \
  -H "Content-Type: application/json" \
  -d '{"posts": [...]}'
```

## Configuration

| Key | Description |
|-----|-------------|
| `openrouter_api_key` | For AI analysis (get from openrouter.ai) |
| `firecrawl_api_key` | For enhanced scraping |
| `discord_webhook` | Discord notifications |
| `slack_webhook` | Slack notifications |
| `notion_token` | Notion integration |
| `notion_db_id` | Notion database ID |

## Integrations

### Notion Database Schema

Create a database with:
- Name (title)
- Subreddit (text)
- URL (url)
- Score (number)
- Intent (select)
- Problem (text)
- Workaround (text)
- Monetization (number)
- Opportunity (text)

### n8n Workflow

Import `n8n-workflow.json` in n8n for visual automation.

### LangGraph Agent

Run with:
```bash
pip install langgraph langchain-openai
python3 langgraph_agent.py --subreddits shopify notion --openrouter-key sk-...
```

## Tech Stack

| Component | Tool |
|-----------|------|
| Scraper | Reddit JSON API / Firecrawl |
| Filter | Keyword-based |
| Analyzer | OpenRouter (Gemini/Claude/GPT) |
| Agent | LangGraph |
| Automation | n8n |
| Output | Notion, Slack, Discord |

## Files

```
reddit-ai-scraper/
├── server.py           # Main HTTP server with AI
├── index.html         # Browser UI
├── langgraph_agent.py # LangGraph agent
├── n8n-workflow.json  # n8n automation
├── install.sh         # Quick start
├── README.md          # This file
├── make.md           # Full documentation
└── changelog.md      # Version history
```

## License

MIT
