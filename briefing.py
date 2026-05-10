import os
import requests
import feedparser
from datetime import datetime
import openai

# ------------------------------------------------------------
# CONFIGURATION – these values will come from GitHub Secrets
# ------------------------------------------------------------
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

openai.api_key = OPENAI_API_KEY

# ------------------------------------------------------------
# 1. FETCH RSS NEWS (AI industry & agentic AI)
# ------------------------------------------------------------
rss_feeds = [
    "https://openai.com/blog/rss.xml",
    "https://www.anthropic.com/news/rss.xml",
    "https://techcrunch.com/tag/artificial-intelligence/feed/"
]

all_articles = []
for feed_url in rss_feeds:
    feed = feedparser.parse(feed_url)
    for entry in feed.entries[:5]:   # take max 5 per feed
        all_articles.append({
            "title": entry.title,
            "link": entry.link,
            "summary": entry.get("summary", "")[:300]
        })

# ------------------------------------------------------------
# 2. FETCH TOP 3 TRENDING AI GITHUB REPOS (last 24h)
# ------------------------------------------------------------
github_url = "https://api.github.com/search/repositories?q=ai+agent+llm&sort=stars&order=desc&per_page=3"
headers = {"Accept": "application/vnd.github.v3+json"}
response = requests.get(github_url, headers=headers)
repos = response.json().get("items", [])

trending = []
for repo in repos:
    trending.append({
        "name": repo["full_name"],
        "url": repo["html_url"],
        "description": repo["description"] or "",
        "stars": repo["stargazers_count"],
        "today_gain": repo.get("stargazers_count", 0)  # note: real 24h gain requires extra API call; for a novice, showing total stars is simpler
    })

# ------------------------------------------------------------
# 3. BUILD THE PROMPT FOR OPENAI (high‑signal filter)
# ------------------------------------------------------------
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

Style: professional, objective, bullet points. Remove marketing fluff ("revolutionary", "game‑changing"). If an item is hype or lacks evidence, skip it.
"""

# ------------------------------------------------------------
# 4. CALL OPENAI TO GENERATE THE BRIEFING
# ------------------------------------------------------------
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",   # cheapest, works well for summarisation
    messages=[
        {"role": "system", "content": "You are a cautious, fact‑based AI research analyst."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.3
)

briefing_text = response.choices[0].message.content

# ------------------------------------------------------------
# 5. SEND TO TELEGRAM (or Discord – see alternative below)
# ------------------------------------------------------------
def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

send_to_telegram(f"📡 *AI Intelligence Briefing – {datetime.now().strftime('%Y-%m-%d')}*\n\n{briefing_text}")
