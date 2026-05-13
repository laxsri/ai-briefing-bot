import os
import requests
import feedparser
from datetime import datetime
from groq import Groq  # need to install groq

print("Starting...")

# Secrets
groq_api_key = os.environ.get("GROQ_API_KEY")
bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
chat_id = os.environ.get("TELEGRAM_CHAT_ID")

if not groq_api_key:
    raise Exception("Missing GROQ_API_KEY")
if not bot_token:
    raise Exception("Missing TELEGRAM_BOT_TOKEN")
if not chat_id:
    raise Exception("Missing TELEGRAM_CHAT_ID")

client = Groq(api_key=groq_api_key)

# RSS (same as before)
feeds = [
    "https://openai.com/blog/rss.xml",
    "https://www.anthropic.com/news/rss.xml",
    "https://techcrunch.com/tag/artificial-intelligence/feed/"
    "https://openai.com/news/rss.xml",
    "https://www.anthropic.com/rss.xml",
    "https://deepmind.google/blog/rss.xml",
    "https://ai.meta.com/blog/rss/",
    "https://huggingface.co/blog/feed.xml",
    "https://www.microsoft.com/en-us/research/feed/",
    "https://aws.amazon.com/blogs/ai/feed/",
    "https://blog.google/technology/ai/rss/",
    "https://mistral.ai/feed.xml",
    "https://rss.arxiv.org/rss/cs.AI",
    "https://rss.arxiv.org/rss/cs.CL",
    "https://rss.arxiv.org/rss/cs.LG",
    "https://ai.stanford.edu/blog/feed.xml",
    "https://bair.berkeley.edu/blog/feed.xml",
    "https://blog.allenai.org/feed",
    "https://www.jmlr.org/jmlr.xml",
    "https://techcrunch.com/tag/artificial-intelligence/feed/",
    "https://www.wired.com/feed/tag/ai/latest/rss",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "https://feeds.arstechnica.com/arstechnica/features/",
    "https://venturebeat.com/category/ai/feed/",
    "https://www.technologyreview.com/topic/artificial-intelligence/feed",
    "https://artificialintelligence-news.com/feed/",
    "https://www.deeplearning.ai/the-batch/feed/",
    "https://importai.substack.com/feed",
    "https://simonwillison.net/atom/everything/",
    "https://lilianweng.github.io/index.xml",
    "https://www.oneusefulthing.org/feed",
    "https://bensbites.beehiiv.com/feed",
    "https://www.oreilly.com/radar/topics/ai/feed/index.xml",
    "https://news.ycombinator.com/rss",
    "https://www.reddit.com/r/MachineLearning/.rss",
    "https://www.reddit.com/r/LocalLLaMA/.rss",
    "https://www.marktechpost.com/feed/",
   
]
articles = []
for url in feeds:
    try:
        f = feedparser.parse(url)
        for e in f.entries[:5]:
            # Create a markdown link: [Title](URL)
            articles.append(f"- [{e.title}]({e.link})")
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

prompt = f"""
Today is {datetime.now().strftime('%Y-%m-%d')}.

Here are the latest AI news headlines with links:
{news_text}

Top 3 trending AI GitHub repos:
{trending_text}

Your task: Write a daily "AI Intelligence Briefing" with four sections:
1. Latest AI Industry News – For each news item, write a 1‑sentence summary and include the original link. Use markdown format: [Headline](URL). Do not omit any link.
2. Agentic AI & Use Cases – Same rule: include source links if available.
3. Newer Offerings / Apps – Include links to launch announcements.
4. GitHub Trending – A table with columns: Repository | Description | Stars | URL (make the repo name a clickable link).

Rules:
- Be professional, concise, objective.
- Skip hype words.
- Every claim must be traceable via the provided link.
- If a link is not available for a specific item, write "No link available".
"""

# Call Groq (free model: llama-3.3-70b-versatile)
response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
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
