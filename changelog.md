# Changelog

## 2026-03-17 - v2.0.0

### Major Updates - AI Agentic Pipeline

Added full implementation matching the original problem statement:

#### ✅ Architecture Implemented

1. **Ingestor (Scraper)** 
   - Reddit JSON API (free, no auth)
   - Firecrawl integration ready

2. **Filter (Router)**
   - Keyword-based intent detection
   - High/medium intent classification
   - 20+ target subreddits

3. **Analyzer (LLM)**
   - OpenRouter integration
   - Pain point extraction prompt
   - Extracts: Problem, Workaround, Monetization Score, Solution, Target User

4. **Database**
   - JSON files in ~/.reddit-ai-scraper/data
   - Notion export
   - Slack/Discord webhooks

#### ✅ Integrations

- **Discord** - Webhook notifications with AI analysis
- **Slack** - Daily digest with opportunities
- **Notion** - Full database export with all fields
- **CSV/JSON** - Export functionality

#### ✅ n8n Workflow

- `n8n-workflow.json` - Visual automation workflow
- Schedule-triggered scanning
- AI analysis node
- Slack/Notion outputs

#### ✅ LangGraph Agent

- `langgraph_agent.py` - Full agentic pipeline
- Multi-stage reasoning
- Configurable via CLI
- Direct Notion/Slack output

### Files Created/Updated

```
reddit-ai-scraper/
├── server.py           # v2.0 - AI analysis + Firecrawl
├── index.html         # AI checkbox + analysis display
├── langgraph_agent.py # LangGraph implementation
├── n8n-workflow.json  # n8n automation
├── README.md          # Updated
├── make.md           # Full documentation
└── changelog.md     # This file
```

### AI Analysis Output

The AI now extracts:

```json
{
  "frustration": "User can't automate inventory sync",
  "workaround": "Using messy spreadsheet",
  "monetization": 8,
  "opportunity": "Shopify inventory automation",
  "target_user": "Shopify store owners"
}
```

### Usage

```bash
# Browser UI with AI
python3 server.py
# Open http://localhost:8080
# Check "Enable AI Analysis"

# LangGraph Agent
pip install langgraph langchain-openai
python3 langgraph_agent.py --subreddits shopify notion
```

## v1.0.0 - 2026-03-17

- Initial release
- Basic scanning
- CSV/JSON export
- Webhooks
