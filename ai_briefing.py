import os
import requests
import feedparser
from datetime import datetime
from openai import OpenAI

print("Starting...")

# Secrets
api_key = os.environ.get("DEEPSEEK_API_KEY")
bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
chat_id = os.environ.get("TELEGRAM_CHAT_ID")

if not api_key:
    raise Exception("Missing DEEPSEEK_API_KEY")
if not bot_token:
    raise Exception("Missing TELEGRAM_BOT_TOKEN")
if not chat_id:
    raise Exception("Missing TELEGRAM_CHAT_ID")

client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")

# RSS
feeds = [
    "https://openai.com/blog/rss.xml",
    "https://www.anthropic.com/news/rss.xml",
    "https://techcrunch.com/tag/artificial-intelligence/feed/"
]

articles = []
for url in feeds:
    try:
        f = feedparser.parse(url)
        for e in f.entries[:5]:
            articles.append(f"- {e.title} ({e.link})")
    except:
        pass

news_text = "\n".join(articles) if articles else "No news fetched."

# GitHub
gh_url = "https://api.github.com/search/repositories?q=ai+agent+llm&sort=stars&order=desc&per_page=3"
resp = requests.get(gh_url, headers={"Accept": "application/vnd.github.v3+json"})
repos = resp.json().get("items", [])
trending_text = ""
for idx, repo in enumerate(repos, 1):
    trending_text += f"{idx}. [{repo['full_name']}]({repo['html_url']}) – {repo.get('description', '')} – ⭐ {repo['stargazers_count']}\n"

# Build prompt (classic string concatenation, no f‑string issues)
prompt = """
Today is """ + datetime.now().strftime('%Y-%m-%d') + """.

Here are the latest AI news headlines:
""" + news_text + """

Top 3 trending AI GitHub repos:
""" + trending_text + """

Your task: Write a daily "AI Intelligence Briefing" with four sections:
1. Latest AI Industry News – measurable claims, regulations, launches.
2. Agentic AI & Use Cases – real deployments, no hype.
3. Newer Offerings / Apps – new tools.
4. GitHub Trending – a table with repo name, description, stars.

Be professional, concise, objective. Skip hype words. Only include items with evidence.
"""

# Call DeepSeek
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "You are a fact‑based AI analyst."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.3
)
briefing = response.choices[0].message.content

# Send to Telegram
url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
payload = {
    "chat_id": chat_id,
    "text": f"📡 *AI Intelligence Briefing – {datetime.now().strftime('%Y-%m-%d')}*\n\n{briefing}",
    "parse_mode": "Markdown"
}
r = requests.post(url, json=payload)
if r.status_code != 200:
    raise Exception(f"Telegram error: {r.text}")

print("✅ Done")
