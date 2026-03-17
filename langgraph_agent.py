#!/usr/bin/env python3
"""
Reddit Pain Point Scanner - LangGraph Agent
Multi-stage agentic pipeline for Reddit market research
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import TypedDict, List, Optional

try:
    from langgraph.graph import StateGraph, END
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError:
    print("Installing dependencies...")
    os.system("pip install langgraph langchain-openai -q")
    from langgraph.graph import StateGraph, END
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage


class AgentState(TypedDict):
    posts: List[dict]
    filtered_posts: List[dict]
    analyzed_posts: List[dict]
    subreddit: str
    config: dict


HIGH_INTENT_KEYWORDS = [
    "is there a tool", "looking for a tool", "need a tool", "recommend a tool",
    "how do i automate", "can i automate", "is there a way to", "why isn't there",
    "tired of", "sick of", "hate it when", "manually", "tedious", "repetitive",
    "using spreadsheet for", "using excel for", "workaround", "no good solution",
]

PAIN_POINT_ANALYSIS_PROMPT = """You are a product researcher analyzing Reddit posts for software business opportunities.

Analyze this Reddit post and extract:

1. CORE_FRUSTRATION: What specific problem is the user trying to solve? (1-2 sentences)

2. CURRENT_WORKAROUND: How are they currently solving this problem?

3. MONETIZATION_SCORE: Rate 1-10 how much time/money this costs them (10 = huge opportunity)

4. SOFTWARE_OPPORTUNITY: What type of software could solve this?

5. TARGET_USER: Who experiences this problem?

Return valid JSON with these exact keys only."""


def fetch_reddit_posts(subreddit: str, limit: int = 25) -> List[dict]:
    """Stage 1: Ingestor - Fetch posts from subreddit"""
    from urllib.request import urlopen, Request
    
    url = f"https://www.reddit.com/r/{subreddit}/rising.json?limit={limit}"
    headers = {"User-Agent": "RedditPainPointScanner/1.0"}
    
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            posts = data.get("data", {}).get("children", [])
            
            return [
                {
                    "id": p.get("data", {}).get("id"),
                    "title": p.get("data", {}).get("title"),
                    "body": p.get("data", {}).get("selftext", ""),
                    "subreddit": subreddit,
                    "url": f"https://reddit.com{p.get('data', {}).get('permalink')}",
                    "score": p.get("data", {}).get("score", 0),
                }
                for p in posts
            ]
    except Exception as e:
        print(f"Error fetching r/{subreddit}: {e}")
        return []


def filter_posts(posts: List[dict]) -> List[dict]:
    """Stage 2: Router/Filter - Filter for high-intent posts"""
    filtered = []
    
    for post in posts:
        content = (post.get("title", "") + " " + post.get("body", "")).lower()
        
        if any(kw in content for kw in HIGH_INTENT_KEYWORDS):
            matched = [kw for kw in HIGH_INTENT_KEYWORDS if kw in content]
            post["matched_keywords"] = matched
            filtered.append(post)
    
    return filtered


def analyze_pain_points(posts: List[dict], config: dict) -> List[dict]:
    """Stage 3: Analyzer - Use LLM to extract pain points"""
    api_key = config.get("openrouter_api_key") or os.environ.get("OPENROUTER_API_KEY")
    
    if not api_key:
        print("No OpenRouter API key - skipping AI analysis")
        return posts
    
    model = config.get("ai_model", "google/gemini-2.0-flash-001")
    
    llm = ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=0.3,
    )
    
    analyzed = []
    
    for post in posts[:10]:
        prompt = f"""{PAIN_POINT_ANALYSIS_PROMPT}

Reddit Post:
Title: {post.get('title')}
Body: {post.get('body', '')[:1000]}"""
        
        try:
            messages = [
                SystemMessage(content="You are a product researcher."),
                HumanMessage(content=prompt)
            ]
            
            response = llm.invoke(messages)
            content = response.content
            
            try:
                analysis = json.loads(content)
            except:
                analysis = {"raw_analysis": content[:500]}
            
            post["ai_analysis"] = analysis
            print(f"✓ Analyzed: {post.get('title')[:50]}...")
            
        except Exception as e:
            post["ai_analysis"] = {"error": str(e)}
            print(f"✗ Error: {e}")
        
        analyzed.append(post)
        time.sleep(0.5)
    
    return analyzed


def save_to_notion(posts: List[dict], config: dict) -> dict:
    """Stage 4: Output - Save to Notion"""
    from urllib.request import urlopen, Request
    
    token = config.get("notion_token")
    db_id = config.get("notion_db_id")
    
    if not token or not db_id:
        return {"error": "No Notion credentials"}
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    created = 0
    for post in posts[:10]:
        analysis = post.get("ai_analysis", {})
        
        data = {
            "parent": {"database_id": db_id},
            "properties": {
                "Name": {"title": [{"text": {"content": post.get("title", "")[:100]}}]},
                "Subreddit": {"rich_text": [{"text": {"content": post.get("subreddit", "")}}]},
                "URL": {"url": post.get("url", "")},
                "Score": {"number": post.get("score", 0)},
                "Problem": {"rich_text": [{"text": {"content": analysis.get("CORE_FRUSTRATION", "")[:200]}}]},
                "Workaround": {"rich_text": [{"text": {"content": analysis.get("CURRENT_WORKAROUND", "")[:200]}}]},
                "Monetization": {"number": analysis.get("MONETIZATION_SCORE", 0)},
                "Opportunity": {"rich_text": [{"text": {"content": analysis.get("SOFTWARE_OPPORTUNITY", "")[:200]}}]},
            }
        }
        
        try:
            req = Request("https://api.notion.com/v1/pages",
                         data=json.dumps(data).encode(), headers=headers, method="POST")
            with urlopen(req, timeout=10):
                created += 1
        except Exception as e:
            print(f"Notion error: {e}")
    
    return {"created": created}


def send_slack_digest(posts: List[dict], config: dict) -> dict:
    """Send daily digest to Slack"""
    from urllib.request import urlopen, Request
    
    webhook = config.get("slack_webhook")
    
    if not webhook:
        return {"error": "No Slack webhook"}
    
    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": "🔥 Software Ideas Digest"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"Found *{len(posts)}* opportunities"}},
        {"type": "divider"}
    ]
    
    for p in posts[:5]:
        analysis = p.get("ai_analysis", {})
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{p.get('title', '')[:60]}*\n💰 Score: {analysis.get('MONETIZATION_SCORE', '?')}/10\n<{p.get('url')}|View>"
            }
        })
    
    try:
        req = Request(webhook, data=json.dumps({"blocks": blocks}).encode(),
                     headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(req, timeout=10):
            return {"status": "sent"}
    except Exception as e:
        return {"error": str(e)}


def run_agent(subreddits: List[str], config: dict):
    """Run the full agent pipeline"""
    print("=" * 50)
    print("Reddit Pain Point Scanner - LangGraph Agent")
    print("=" * 50)
    
    all_filtered = []
    
    for sr in subreddits:
        print(f"\n📥 Stage 1: Fetching r/{sr}...")
        posts = fetch_reddit_posts(sr)
        print(f"   Got {len(posts)} posts")
        
        print(f"   🔍 Stage 2: Filtering for pain points...")
        filtered = filter_posts(posts)
        print(f"   Found {len(filtered)} high-intent posts")
        
        all_filtered.extend(filtered)
    
    if not all_filtered:
        print("\n❌ No high-intent posts found")
        return
    
    print(f"\n🧠 Stage 3: AI Analysis ({len(all_filtered)} posts)")
    analyzed = analyze_pain_points(all_filtered, config)
    
    high_opportunity = [
        p for p in analyzed 
        if p.get("ai_analysis", {}).get("MONETIZATION_SCORE", 0) >= 7
    ]
    
    print(f"\n💎 High opportunity posts: {len(high_opportunity)}")
    
    print("\n💾 Stage 4: Saving to outputs...")
    
    if config.get("notion_token"):
        result = save_to_notion(analyzed, config)
        print(f"   Notion: {result}")
    
    if config.get("slack_webhook"):
        result = send_slack_digest(analyzed, config)
        print(f"   Slack: {result}")
    
    DATA_DIR = Path.home() / ".reddit-ai-scraper" / "data"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(DATA_DIR / f"agent_scan_{ts}.json", "w") as f:
        json.dump({
            "subreddits": subreddits,
            "total_posts": len(all_filtered),
            "analyzed": analyzed,
            "high_opportunity": high_opportunity
        }, f, indent=2)
    
    print(f"\n✅ Done! Saved to {DATA_DIR}")
    print("=" * 50)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Reddit Pain Point Scanner - LangGraph Agent")
    parser.add_argument("--subreddits", nargs="+", default=["shopify", "notion", "smallbusiness"],
                       help="Subreddits to scan")
    parser.add_argument("--openrouter-key", help="OpenRouter API key")
    parser.add_argument("--notion-token", help="Notion integration token")
    parser.add_argument("--notion-db", help="Notion database ID")
    parser.add_argument("--slack-webhook", help="Slack webhook URL")
    parser.add_argument("--ai-model", default="google/gemini-2.0-flash-001", help="AI model to use")
    
    args = parser.parse_args()
    
    config = {
        "openrouter_api_key": args.openrouter_key or os.environ.get("OPENROUTER_API_KEY"),
        "notion_token": args.notion_token or os.environ.get("NOTION_TOKEN"),
        "notion_db_id": args.notion_db or os.environ.get("NOTION_DB_ID"),
        "slack_webhook": args.slack_webhook or os.environ.get("SLACK_WEBHOOK_URL"),
        "ai_model": args.ai_model,
    }
    
    run_agent(args.subreddits, config)


if __name__ == "__main__":
    main()
