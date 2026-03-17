#!/usr/bin/env python3
"""
Reddit AI Scraper - Full Implementation with AI Analysis
Enhanced with LLM-powered pain point extraction
"""

import json
import sys
import time
import csv
import io
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import urlparse

CONFIG_DIR = Path.home() / ".reddit-ai-scraper"
CONFIG_FILE = CONFIG_DIR / "config.json"
DATA_DIR = CONFIG_DIR / "data"

SUBREDDITS = {
    "shopify": "E-commerce", "shopifyapps": "Shopify apps", "dropshipping": "Dropshipping",
    "smallbusiness": "Small business", "entrepreneur": "Entrepreneurship", "startups": "Startups",
    "sideproject": "Side projects", "saas": "SaaS", "webdev": "Web dev", "python": "Python",
    "javascript": "JavaScript", "reactjs": "React", "aws": "AWS", "notion": "Notion",
    "n8n": "n8n", "zapier": "Zapier", "airtable": "Airtable", "productivity": "Productivity",
    "freelance": "Freelance", "indiehackers": "Indie hackers", "bootstrapped": "Bootstrapped",
    "excel": "Excel", "realestate": "Real Estate",
}

HIGH_INTENT = [
    "is there a tool", "is there an app", "looking for a tool", "recommend a tool", "need a tool",
    "how do i automate", "can i automate", "is there a way to", "why isn't there", "there should be",
    "i wish there was", "tired of", "sick of", "hate it when", "manually", "tedious", "repetitive",
    "using spreadsheet for", "using excel for", "workaround", "no good solution",
]

MEDIUM_INTENT = ["how do i", "how can i", "help me", "looking for", "struggling with", "having trouble", "any ideas"]

PAIN_POINT_PROMPT = """You are a product researcher analyzing Reddit posts for software business opportunities.

Analyze this Reddit post and extract:

1. CORE FRUSTRATION: What specific problem is the user trying to solve? (1-2 sentences)

2. CURRENT WORKAROUND: How are they currently solving this problem? (e.g., "I use a messy spreadsheet", "I manually copy-paste data")

3. MONETIZATION SCORE: Rate 1-10 how much time/money this problem costs them (10 = huge opportunity)

4. SOFTWARE OPPORTUNITY: What type of software could solve this? (e.g., "Automate X", "Integration tool", "Dashboard")

5. TARGET USER: Who experiences this problem? (e.g., "Shopify store owners", "Freelancers")

Return ONLY valid JSON with these exact keys:
{"frustration": "...", "workaround": "...", "monetization": 1-10, "opportunity": "...", "target_user": "..."}"""


def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}


def save_config(config):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def fetch_reddit(subreddit, limit=25):
    url = f"https://www.reddit.com/r/{subreddit}/rising.json?limit={limit}"
    headers = {"User-Agent": "RedditAIScraper/1.0"}
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data.get("data", {}).get("children", [])
    except:
        return []


def fetch_with_firecrawl(url):
    """Use Firecrawl API for better scraping"""
    config = load_config()
    api_key = config.get("firecrawl_api_key")
    
    if not api_key:
        return None
    
    try:
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        data = {"url": url, "formats": ["markdown"]}
        req = Request("https://api.firecrawl.dev/v1/scrape", 
                     data=json.dumps(data).encode(), headers=headers, method="POST")
        with urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            return result.get("data", {}).get("markdown", "")
    except Exception as e:
        print(f"Firecrawl error: {e}")
        return None


def analyze_with_ai(posts, model="google/gemini-2.0-flash-001"):
    """Use LLM to extract pain points from posts"""
    config = load_config()
    api_key = config.get("openrouter_api_key")
    
    if not api_key:
        return [{"error": "OpenRouter API key not configured"}]
    
    analyzed = []
    
    for post in posts[:10]:
        prompt = f"{PAIN_POINT_PROMPT}\n\nReddit Post:\nTitle: {post.get('title')}\nBody: {post.get('body', '')[:1000]}"
        
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://reddit-ai-scraper.local",
                "X-Title": "Reddit AI Scraper"
            }
            data = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500
            }
            req = Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=json.dumps(data).encode(),
                headers=headers,
                method="POST"
            )
            with urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode())
                content = result["choices"][0]["message"]["content"]
                
                try:
                    analysis = json.loads(content)
                except:
                    analysis = {"raw_analysis": content[:500]}
                
                post["ai_analysis"] = analysis
        except Exception as e:
            post["ai_analysis"] = {"error": str(e)}
        
        analyzed.append(post)
        time.sleep(0.5)
    
    return analyzed


def scan_subreddits(subreddits, limit=25, use_ai=False):
    results = []
    high = []
    medium = []
    
    for sr in subreddits:
        posts = fetch_reddit(sr, limit)
        for post_data in posts:
            post = post_data.get("data", {})
            title = (post.get("title", "") or "").lower()
            body = (post.get("selftext", "") or "").lower()
            content = title + " " + body
            
            is_high = any(kw in content for kw in HIGH_INTENT)
            is_med = any(kw in content for kw in MEDIUM_INTENT)
            
            pdata = {
                "id": post.get("id"),
                "title": post.get("title"),
                "body": post.get("selftext", ""),
                "subreddit": sr,
                "url": f"https://reddit.com{post.get('permalink')}",
                "score": post.get("score", 0),
                "comments": post.get("num_comments", 0),
                "author": post.get("author"),
                "intent": "high" if is_high else ("medium" if is_med else "low"),
                "matched_keywords": [kw for kw in HIGH_INTENT + MEDIUM_INTENT if kw in content]
            }
            
            if is_high:
                high.append(pdata)
            elif is_med:
                medium.append(pdata)
            results.append(pdata)
        
        time.sleep(1)
    
    analyzed_high = high
    if use_ai and high:
        print("Running AI analysis on high-intent posts...")
        analyzed_high = analyze_with_ai(high)
    
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(DATA_DIR / f"scan_{ts}.json", "w") as f:
        json.dump({
            "results": results, 
            "high": analyzed_high, 
            "medium": medium, 
            "subreddits": subreddits,
            "ai_analyzed": use_ai
        }, f, indent=2)
    
    return {
        "subreddits": subreddits, 
        "total": len(results), 
        "high_intent": len(high), 
        "medium_intent": len(medium),
        "ai_analyzed": use_ai,
        "high": analyzed_high[:20]
    }


def send_discord(webhook_url, posts):
    if not webhook_url or not posts:
        return {"error": "Missing webhook or posts"}
    
    embeds = []
    for p in posts[:5]:
        analysis = p.get("ai_analysis", {})
        monetization = analysis.get("monetization", "?")
        opportunity = analysis.get("opportunity", "Software solution")
        
        embed = {
            "title": p.get("title", "")[:100],
            "description": f"**{opportunity}**\n💰 Monetization: {monetization}/10",
            "url": p.get("url", ""),
            "color": 0xFF6B6B,
            "fields": [
                {"name": "Subreddit", "value": f"r/{p.get('subreddit')}", "inline": True},
                {"name": "Score", "value": str(p.get("score", 0)), "inline": True},
            ]
        }
        
        if analysis.get("frustration"):
            embed["fields"].append({"name": "Problem", "value": analysis["frustration"][:200], "inline": False})
        
        embeds.append(embed)
    
    try:
        req = Request(webhook_url, data=json.dumps({"embeds": embeds}).encode(), 
                     headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(req, timeout=10):
            return {"status": "sent", "count": len(embeds)}
    except Exception as e:
        return {"error": str(e)}


def send_slack(webhook_url, posts):
    if not webhook_url or not posts:
        return {"error": "Missing webhook or posts"}
    
    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": "🔥 Software Ideas Found!"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"Found *{len(posts)}* opportunities"}},
        {"type": "divider"}
    ]
    
    for p in posts[:5]:
        analysis = p.get("ai_analysis", {})
        title = p.get("title", "")[:80]
        monetization = analysis.get("monetization", "?")
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{title}*\n💰 Score: {monetization}/10 | r/{p.get('subreddit')} | {p.get('score')} pts\n<{p.get('url')}|View Post>"
            }
        })
    
    try:
        req = Request(webhook_url, data=json.dumps({"blocks": blocks}).encode(), 
                     headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(req, timeout=10):
            return {"status": "sent", "count": len(blocks)}
    except Exception as e:
        return {"error": str(e)}


def export_notion(posts, token, db_id):
    if not token or not db_id:
        return {"error": "Missing token or DB ID"}
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    created = []
    for p in posts[:10]:
        analysis = p.get("ai_analysis", {})
        
        data = {
            "parent": {"database_id": db_id},
            "properties": {
                "Name": {"title": [{"text": {"content": p.get("title", "")[:100]}}]},
                "Subreddit": {"rich_text": [{"text": {"content": p.get("subreddit", "")}}]},
                "URL": {"url": p.get("url", "")},
                "Score": {"number": p.get("score", 0)},
                "Intent": {"select": {"name": p.get("intent", "low")}},
                "Problem": {"rich_text": [{"text": {"content": analysis.get("frustration", "")[:200]}}]},
                "Workaround": {"rich_text": [{"text": {"content": analysis.get("workaround", "")[:200]}}]},
                "Monetization": {"number": analysis.get("monetization", 0)},
                "Opportunity": {"rich_text": [{"text": {"content": analysis.get("opportunity", "")[:200]}}]},
            }
        }
        
        try:
            req = Request("https://api.notion.com/v1/pages",
                         data=json.dumps(data).encode(), headers=headers, method="POST")
            with urlopen(req, timeout=10):
                created.append(p.get("id"))
        except Exception as e:
            print(f"Notion error: {e}")
    
    return {"created": len(created)}


HTML_FILE = Path(__file__).parent / "index.html"

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == "/":
            if HTML_FILE.exists():
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(HTML_FILE.read_text().encode())
            else:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"name": "Reddit AI Scraper", "version": "2.0"}).encode())
        
        elif path == "/list":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(SUBREDDITS).encode())
        
        elif path == "/results":
            if DATA_DIR.exists():
                files = sorted(DATA_DIR.glob("scan_*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:10]
                results = []
                for f in files:
                    data = json.loads(f.read_text())
                    results.append({
                        "file": f.name, 
                        "total": len(data.get("results", [])), 
                        "high": len(data.get("high", [])),
                        "ai_analyzed": data.get("ai_analyzed", False)
                    })
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(results).encode())
            else:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b"[]")
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        data = json.loads(body) if body else {}
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == "/scan":
            subs = data.get("subreddits", ["shopify", "notion", "smallbusiness"])
            use_ai = data.get("ai_analyze", False)
            result = scan_subreddits(subs, data.get("limit", 25), use_ai)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        
        elif path == "/analyze":
            posts = data.get("posts", [])
            model = data.get("model", "google/gemini-2.0-flash-001")
            result = analyze_with_ai(posts, model)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        
        elif path == "/config":
            config = load_config()
            config.update(data)
            save_config(config)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        
        elif path == "/firecrawl":
            url = data.get("url")
            result = fetch_with_firecrawl(url)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"markdown": result}).encode())
        
        elif path == "/webhook/discord":
            cfg = load_config()
            result = send_discord(cfg.get("discord_webhook"), data.get("posts", []))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        
        elif path == "/webhook/slack":
            cfg = load_config()
            result = send_slack(cfg.get("slack_webhook"), data.get("posts", []))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        
        elif path == "/notion":
            cfg = load_config()
            result = export_notion(
                data.get("posts", []),
                cfg.get("notion_token"),
                cfg.get("notion_db_id")
            )
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        print(f"[{args[0]}] {format % args}")


def run_server(port=8080):
    print(f"Reddit AI Scraper v2.0 - http://localhost:{port}")
    print("Enhanced with AI Pain Point Analysis")
    print("Open browser to use GUI")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    run_server(int(sys.argv[1]) if len(sys.argv) > 1 else 8080)
