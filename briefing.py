import os
import requests
import feedparser
from datetime import datetime
from openai import OpenAI  # Keep this import, we'll just use it differently

# ------------------------------------------------------------
# CONFIGURATION – using DeepSeek
# ------------------------------------------------------------
# Change the line that gets your API key to use the new secret name
DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# --- The only significant change ---
# Initialize the OpenAI client, but point it to DeepSeek's base URL
# and use your DeepSeek API key.
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1"  # DeepSeek's OpenAI-compatible endpoint
)
# ------------------------------------

# ------------------------------------------------------------
# ... (The rest of the script for fetching RSS and GitHub data remains exactly the same) ...
# ------------------------------------------------------------

# ------------------------------------------------------------
# 3. BUILD THE PROMPT FOR DEEPSEEK (using the same prompt logic)
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
# 4. CALL DEEPSEEK (via the OpenAI client library)
# ------------------------------------------------------------
response = client.chat.completions.create(
    model="deepseek-chat",  # This is DeepSeek's latest V3 model
    messages=[
        {"role": "system", "content": "You are a cautious, fact‑based AI research analyst."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.3
)

briefing_text = response.choices[0].message.content

# ------------------------------------------------------------
# 5. SEND TO TELEGRAM (This part remains unchanged)
# ------------------------------------------------------------
# ... (keep your existing send_to_telegram function here) ...
