import os
import requests
import feedparser
from datetime import datetime
from groq import Groq

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

# ── Telegram helper: split & send ──────────────────────────────────────
TELEGRAM_MAX = 4096  # Telegram's hard character limit per message


def split_message(text, max_len=TELEGRAM_MAX):
    """Split text into chunks that fit Telegram's limit.
    Tries to break at paragraph boundaries first, then line boundaries,
    then hard-cuts as a last resort."""
    if len(text) <= max_len:
        return [text]

    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break

        # Try to split at a double-newline (paragraph break)
        cut = text.rfind("\n\n", 0, max_len)
        if cut == -1:
            # Fall back to single newline
            cut = text.rfind("\n", 0, max_len)
        if cut == -1:
            # Last resort: hard cut
            cut = max_len

        chunks.append(text[:cut])
        text = text[cut:].lstrip("\n")

    return chunks


def send_telegram(text, parse_mode="Markdown"):
    """Send a message to Telegram, automatically splitting if too long."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    chunks = split_message(text)

    for i, chunk in enumerate(chunks, 1):
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": parse_mode,
        }
        r = requests.post(url, json=payload)
        if r.status_code != 200:
            # If Markdown parsing fails, retry without formatting
            payload["parse_mode"] = None
            r = requests.post(url, json=payload)
            if r.status_code != 200:
                raise Exception(
                    f"Telegram error on chunk {i}/{len(chunks)}: {r.text}"
                )
    print(f"  Sent {len(chunks)} message(s) to Telegram.")


# ── RSS feeds ──────────────────────────────────────────────────────────
# NOTE: fixed the missing comma between TechCrunch and OpenAI URLs
feeds = [
    "https://openai.com/blog/rss.xml",
    "https://www.anthropic.com/news/rss.xml",
    "https://techcrunch.com/tag/artificial-intelligence/feed/",  # ← comma was missing
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

MAX_PER_FEED = 3  # keep the briefing manageable
MAX_TOTAL = 60    # hard cap on total articles sent to the LLM

articles = []
for url in feeds:
    try:
        f = feedparser.parse(url)
        for e in f.entries[:MAX_PER_FEED]:
            articles.append(f"- [{e.title}]({e.link})")
    except Exception as exc:
        print(f"  ⚠ Feed failed: {url} — {exc}")

# Cap total to avoid blowing up the LLM context / output
articles = articles[:MAX_TOTAL]
news_text = "\n".join(articles) if articles else "No news fetched."

# ── GitHub trending ────────────────────────────────────────────────────
gh_url = (
    "https://api.github.com/search/repositories"
    "?q=ai+agent+llm&sort=stars&order=desc&per_page=3"
)
trending_text = ""
try:
    resp = requests.get(
        gh_url, headers={"Accept": "application/vnd.github.v3+json"}, timeout=15
    )
    resp.raise_for_status()
    repos = resp.json().get("items", [])
    for idx, repo in enumerate(repos, 1):
        trending_text += (
            f"{idx}. [{repo['full_name']}]({repo['html_url']}) "
            f"– {repo.get('description', '')} – ⭐ {repo['stargazers_count']}\n"
        )
except Exception as exc:
    print(f"  ⚠ GitHub API error: {exc}")
    trending_text = "GitHub data unavailable.\n"

# ── LLM prompt ─────────────────────────────────────────────────────────
prompt = f"""
Today is {datetime.now().strftime('%Y-%m-%d')}.

Here are the latest AI news headlines with links:
{news_text}

Top 3 trending AI GitHub repos:
{trending_text}

Your task: Write a daily "AI Intelligence Briefing" with four sections:
1. Latest AI Industry News – For each news item, write a 1‑sentence summary
   and include the original link. Use markdown: [Headline](URL).
2. Agentic AI & Use Cases – Include source links if available.
3. Newer Offerings / Apps – Include links to launch announcements.
4. GitHub Trending – A table: Repository | Description | Stars | URL
   (make the repo name a clickable link).

Rules:
- Be professional, concise, objective.
- Skip hype words.
- Every claim must be traceable via the provided link.
- If a link is not available, write "No link available".
- Keep the TOTAL output under 3500 characters so it fits a single
  Telegram message when possible.
"""

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "system", "content": "You are a fact‑based AI analyst."},
        {"role": "user", "content": prompt},
    ],
    temperature=0.3,
)
briefing = response.choices[0].message.content

# ── Send ───────────────────────────────────────────────────────────────
header = (
    f"📡 *AI Intelligence Briefing – "
    f"{datetime.now().strftime('%Y-%m-%d')}*\n\n"
)
send_telegram(header + briefing)

print("✅ Done")
