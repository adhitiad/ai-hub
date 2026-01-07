import json

import yfinance as yf

from src.core.llm_analyst import client  # Import Groq client yang sudah ada
from src.core.logger import logger
from src.core.vector_db import save_news_vector


def fetch_market_news(symbol):
    """
    Mengambil berita terbaru terkait simbol tertentu via YFinance.
    """
    try:
        # 1. Ambil Raw News
        ticker = yf.Ticker(symbol)
        news_list = ticker.news

        if not news_list:
            return []

        # 2. Format Data
        formatted_news = []
        for n in news_list[:3]:  # Ambil 3 berita terbaru saja
            formatted_news.append(
                {
                    "title": n.get("title"),
                    "publisher": n.get("publisher"),
                    "link": n.get("link"),
                    "timestamp": n.get("providerPublishTime"),
                }
            )

        return formatted_news
    except Exception as e:
        logger.error(f"News Fetch Error {symbol}: {e}")
        return []


def analyze_news_sentiment(symbol, news_data):
    """
    Mengirim judul berita ke AI (Groq) untuk dinilai sentimennya.
    Output: Score -1.0 (Sangat Negatif) s/d 1.0 (Sangat Positif).
    """
    if not news_data:
        return 0.0, "No News"

    titles = [n["title"] for n in news_data]
    titles_text = "\n".join(f"- {t}" for t in titles)

    system_prompt = """
    You are a Financial Sentiment Analyst. 
    Analyze the following news headlines for the asset.
    Return a JSON with:
    1. "score": float between -1.0 (Bearish) and 1.0 (Bullish).
    2. "summary": One short sentence explaining WHY the market might move.
    """

    user_prompt = f"ASSET: {symbol}\nNEWS:\n{titles_text}"

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        content = completion.choices[0].message.content
        if content is None:
            return 0.0, "No content from AI"

        result = json.loads(content)
        summary = result.get("summary", "Neutral news flow.")
        score = result.get("score", 0.0)

        if news_data:
            save_news_vector(
                symbol=symbol,
                summary=summary,
                sentiment_score=score,
                raw_text=titles_text,
            )

        return score, summary

    except Exception as e:
        logger.error("Sentiment Analysis Error: %s", e)
        return 0.0, "AI Error"
