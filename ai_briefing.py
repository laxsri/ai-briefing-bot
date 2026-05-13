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
##############################################################################

Research Prompt: Viral Products Under ₹300 in India (Past Month Analysis)
Objective: Identify trending viral products sold online in India priced under ₹300, analyze their popularity trends over the past month (April-May 2026), and determine if new products are emerging or if existing ones continue to dominate.
Key Research Areas:
1. E-commerce Platform Analysis

Meesho: Focus on women's ethnic wear (kurtis, sarees), beauty products, mobile accessories, home essentials, and kitchen gadgets
Amazon India: Check bestsellers and "Hot New Releases" sections for products under ₹300
Flipkart: Review trending items and viral products in the budget category

2. Product Categories to Track
Based on current trends, these categories dominate the under-₹300 segment:
Fashion & Beauty:

Women's cotton/rayon kurtis (₹150-₹299)
Beauty combo kits and skincare sets
Fashion jewelry and accessories
Underarm roll-ons and deodorants

Tech & Gadgets:

Mini USB fans, OTG adapters, cable organizers, earbuds cleaning pens Techbydevansh
Mobile phone accessories (cases, pop sockets, screen guards)
Bluetooth speakers (compact models)
3-in-1 charging cables

Home & Kitchen:

Kitchen choppers and organizers
Storage containers and non-stick gadgets PURSHO
Home decor items (wall stickers, LED lights)
Cleaning supplies (magic erasers, microfiber cloths)

3. Social Media Viral Tracking

Instagram Reels: Search hashtags like #MeeshoFinds, #Under300, #ViralProducts2026
YouTube Shorts: Look for haul videos and product reviews
TikTok trends: Search "TikTok made me buy it" for viral product recommendations NimbusPost

4. Trend Analysis Questions

Are the same products from last month still trending, or are new ones taking over?
Which products are achieving 300-1000 orders per day on Meesho? PURSHO
What's driving virality: social media influence, utility, or pricing?
Are seasonal products (summer-related) showing increased demand?

5. Key Metrics to Track

Product review counts and ratings
Search volume trends (Google Trends)
Seller catalog performance
Category-specific spikes (beauty products peaked in December 2025, home essentials in May 2025) Accio

6. Current Market Insights (May 2026)

Women's ethnic wear remains the undisputed leader in volume on Meesho, driven by social media virality Accio
Budget home décor is one of the fastest-growing categories in 2026 PURSHO
Tech accessories under ₹500 are seeing consistent demand
Combo packs (2 for ₹199, 3-piece sets) are driving conversions

7. Actionable Research Steps

Monitor daily: Visit Meesho and Amazon India's "Trending" sections
Social listening: Track viral product hashtags daily
Compare pricing: Check if products maintain ₹299 or below pricing
Review velocity: Products with 100+ reviews in the past month indicate virality
Supplier trends: Watch wholesale markets for new product introductions


Expected Outcome: A comprehensive list of 15-20 viral products under ₹300 with trend direction (stable, rising, or declining), pricing analysis, and insights on whether the market is seeing fresh viral hits or if established products continue dominating.
##############################################################################


#1. Latest AI Industry News – For each news item, write a 1‑sentence summary and include the original link. Use markdown format: [Headline](URL). Do not omit any link.
#2. Agentic AI & Use Cases – Same rule: include source links if available.
#3. Newer Offerings / Apps – Include links to launch announcements.
#4. GitHub Trending – A table with columns: Repository | Description | Stars | URL (make the repo name a clickable link).

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
