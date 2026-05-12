import os
import requests
import feedparser
from datetime import datetime
from openai import OpenAI

# Get secrets from GitHub environment
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Check if any secret is missing
if not DEEPSEEK_API_KEY:
    raise Exception("Missing DEEPSEEK_API_KEY secret")
if not TELEGRAM_BOT_TOKEN:
    raise Exception("Missing TELEGRAM_BOT_TOKEN secret")
if not TELEGRAM_CHAT_ID:
    raise Exception("Missing TELEGRAM_CHAT_ID secret")

# Initialize DeepSeek client
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1"
)

# Fetch RSS feeds
rss_feeds = [
    "https://openai.com/blog/rss.xml",
    "https://www.anthropic.com/news/rss.xml",
    "https://techcrunch.com/tag/artificial-intelligence/feed/"
]

all_articles = []   # <-- defined here, BEFORE any possible error
for feed_url in rss_feeds:
    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:5]:
            all_articles.append({
                "title": entry.title,
                "link": entry.link,
                "summary": entry.get("summary", "")[:300]
            })
    except Exception as e:
        print(f"Warning: Could not fetch {feed_url} – {e}")

# Fetch GitHub trending repos
github_url = "https://api.github.com/search/repositories?q=ai+agent+llm&sort=stars&order=desc&per_page=3"
response = requests.get(github_url, headers={"Accept": "application/vnd.github.v3+json"})
repos = response.json().get("items", [])

trending = []
for repo in repos:
    trending.append({
        "name": repo["full_name"],
        "url": repo["html_url"],
        "description": repo.get("description", ""),
        "stars": repo["stargazers_count"]
    })

# Build prompt
prompt = f"""
Today is {datetime.now().strftime('%Y-%m-%d')}.

Here are raw news headlines and summaries:
{all_articles}

Here are the top 3 GitHub AI repos (name, description, stars):
{trending}

Your job: Produce a daily "AI Intelligence Briefing" with four sections:
1. Latest AI Industry News – keep only items with measurable claims, regulations, or verifiable launches.
2. Agentic AI & Use Cases – focus on real deployments, not hype.
3. Newer Offerings / Apps – only brand‑new tools (launch announcements).
4. GitHub Trending – show a simple table with repo name, description, and stars.

Style: professional, objective, bullet points. Remove marketing fluff. If an item is hype or lacks evidence, skip it.
"""

# Call DeepSeek
try:
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a cautious, fact‑based AI research analyst."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    briefing_text = response.choices[0].message.content
except Exception as e:
    raise Exception(f"DeepSeek API call failed: {e}")

# Send to Telegram
def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    resp = requests.post(url, json=payload)
    if resp.status_code != 200:
        raise Exception(f"Telegram send failed: {resp.text}")

send_to_telegram(f"📡 *AI Intelligence Briefing – {datetime.now().strftime('%Y-%m-%d')}*\n\n{briefing_text}")

print("✅ Briefing sent successfully")
