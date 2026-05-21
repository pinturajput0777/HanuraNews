\import os
import time
import requests
import asyncio
from telegram import Bot
from telegram.request import HTTPXRequest
from groq import Groq

# --- CONFIGURATION (Environment Variables Se Key Uthayega) ---
TELEGRAM_TOKEN = "8771497619:AAHdTxUu1FeEsvD3S4W3PfKwI2rb0XzGmFs"
CHANNEL_ID = "@piut89"

# GitHub security se bachne ke liye keys ko environment variable bana diya hai
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GNEWS_API_KEY = os.environ.get("GNEWS_API_KEY")
MARKETAUX_API_KEY = os.environ.get("MARKETAUX_API_KEY")
LEONARDO_API_KEY = os.environ.get("LEONARDO_API_KEY")

# Initialize Groq Client safely
if GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)
else:
    groq_client = None

posted_titles = set()

# Timeout issue fix karne ke liye explicitly set kiya hai
tg_request = HTTPXRequest(connect_timeout=30.0, read_timeout=30.0)
bot = Bot(token=TELEGRAM_TOKEN, request=tg_request)

def fetch_latest_news():
    """Marketaux aur GNews se latest financial news lane ke liye"""
    if MARKETAUX_API_KEY:
        url_marketaux = f"https://api.marketaux.com/v1/news/all?symbols=TSLA,AMZN,MSFT&filter_entities=true&limit=1&api_token={MARKETAUX_API_KEY}"
        try:
            res = requests.get(url_marketaux, timeout=10).json()
            if res.get("data"):
                news = res["data"][0]
                return news.get("title"), news.get("description")
        except Exception as e:
            print(f"Marketaux Error: {e}")

    if GNEWS_API_KEY:
        url_gnews = f"https://gnews.io/api/v4/search?q=finance OR crypto OR trading&lang=en&max=1&apikey={GNEWS_API_KEY}"
        try:
            res = requests.get(url_gnews, timeout=10).json()
            if res.get("articles"):
                news = res["articles"][0]
                return news.get("title"), news.get("description")
        except Exception as e:
            print(f"GNews Error: {e}")
    
    return None, None

def generate_groq_article(title, description):
    """Groq AI se strict HTML formatting waala post generate karne ke liye"""
    if not groq_client:
        return f"<b>🚨 Breaking News:</b> {title}\n\n{description}"

    prompt = f"""
    You are an expert financial market analyst. Create an engaging, attractive, and short Telegram post based on this news:
    Title: {title}
    Description: {description}

    Requirements:
    1. Write a catchy headline with relevant emojis.
    2. Provide a brief breakdown/analysis in 3-4 short bullet points max.
    3. Keep it highly professional but under 700 characters total.
    4. Include 3-4 relevant financial hashtags at the end (e.g. #Crypto #Trading).
    5. CRITICAL: Use HTML tags for formatting. Use <b>text</b> for bold, and regular text for everything else. Do not use asterisks (*) or underscores (_) anywhere.
    """
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant", 
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=250
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Groq AI Error: {e}")
        return f"<b>🚨 Breaking News:</b> {title}\n\n{description}"

def generate_leonardo_image(title):
    """Image URL generation with fast pollination fallback"""
    clean_title = "".join(c for c in title if c.isalnum() or c.isspace()).replace(" ", "%20")
    return f"https://image.pollinations.ai/p/{clean_title}?width=600&height=600&nofeed=true"

async def post_to_telegram(text, image_url):
    """HTML parse mode ke sath channel par post bhejna"""
    try:
        async with bot:
            await bot.send_photo(chat_id=CHANNEL_ID, photo=image_url, caption=text, parse_mode="HTML")
            print("🎉 Success! Post channel par chala gaya!")
    except Exception as e:
        print(f"Telegram Posting Error: {e}")

async def main():
    print("🚀 Financial Market Automation Bot Shuru Ho Chuka Hai...")
    
    while True:
        title, desc = fetch_latest_news()
        
        if title and title not in posted_titles:
            print(f"📰 Fresh news mili: {title}")
            
            article_text = generate_groq_article(title, desc)
            img_url = generate_leonardo_image(title)
            
            print("Telegram par upload ho raha hai...")
            await post_to_telegram(article_text, img_url)
            
            posted_titles.add(title)
            if len(posted_titles) > 100:
                posted_titles.pop()
        else:
            print("Check kiya: Koi nayi news nahi mili ya duplicate hai.")

        print("Agli news ke liye check 10 mins baad hoga...")
        await asyncio.sleep(600)

if __name__ == "__main__":
    asyncio.run(main())

