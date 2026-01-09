# src/core/news_collector.py

import urllib.parse
from datetime import datetime, timedelta

import feedparser
import nltk
from dateutil import parser
from textblob import TextBlob

# Coba import VADER, jika belum ada download dulu
try:
    from nltk.sentiment.vader import SentimentIntensityAnalyzer

    vader = SentimentIntensityAnalyzer()
except LookupError:
    nltk.download("vader_lexicon")
    from nltk.sentiment.vader import SentimentIntensityAnalyzer

    vader = SentimentIntensityAnalyzer()

# --- KONFIGURASI GOOGLE NEWS ---
BASE_URL = "https://news.google.com/rss/search?q={query}&hl={lang}&gl={region}&ceid={region}:{lang}"


def get_google_news_rss(symbol, asset_type="forex"):
    """
    Mengambil berita terbaru dari Google News via RSS.
    Otomatis menyesuaikan Wilayah & Bahasa berdasarkan aset.
    """
    # 1. Tentukan Query & Region
    # Saham Indo -> Region ID, Bahasa ID
    # Forex/Crypto -> Region US, Bahasa EN

    query = symbol
    lang = "en-US"
    region = "US"

    if asset_type == "stock_indo":
        # Bersihkan simbol (BBCA.JK -> BBCA)
        clean_sym = symbol.replace(".JK", "")
        query = f"Saham {clean_sym} Indonesia"  # Keyword spesifik
        lang = "id-ID"
        region = "ID"
    else:
        # Forex / Crypto
        clean_sym = symbol.replace("=X", "").replace("-USD", "")
        query = f"{clean_sym} price forecast market news"

    # Encode URL
    encoded_query = urllib.parse.quote(query)
    final_url = BASE_URL.format(query=encoded_query, lang=lang, region=region)

    # 2. Fetch RSS
    feed = feedparser.parse(final_url)

    news_items = []

    # Ambil max 5 berita terbaru dalam 24 jam terakhir
    limit_date = datetime.now(datetime.now().astimezone().tzinfo) - timedelta(hours=24)

    for entry in feed.entries[:5]:  # Ambil 5 teratas
        try:
            # Parse tanggal publish
            pub_date = parser.parse(entry.published)

            # Skip berita basi (> 24 jam)
            # if pub_date < limit_date: continue

            news_items.append(
                {
                    "title": entry.title,
                    "link": entry.link,
                    "published": pub_date.strftime("%Y-%m-%d %H:%M"),
                    "source": (
                        entry.source.title
                        if hasattr(entry, "source")
                        else "Google News"
                    ),
                }
            )
        except Exception:
            continue

    return news_items


def analyze_sentiment_vader(text):
    """
    Analisis Sentimen Cepat & Offline (Backup jika LLM mati).
    Return: Score -1.0 (Negatif) s/d 1.0 (Positif)
    """
    try:
        # VADER bagus untuk teks pendek/headline bahasa Inggris
        scores = vader.polarity_scores(text)
        return scores["compound"]
    except:
        # Fallback TextBlob (bisa sedikit handle bahasa lain via translation internal jika perlu)
        return TextBlob(text).sentiment.polarity


def fetch_market_news(symbol, asset_type="forex"):
    """
    Fungsi Utama yang dipanggil oleh Agent.
    """
    # 1. Ambil Berita Google
    raw_news = get_google_news_rss(symbol, asset_type)

    if not raw_news:
        return []

    # 2. Hitung Sentimen Awal per Headline
    processed_news = []
    for item in raw_news:
        # Gabungkan Title untuk analisis
        text_to_analyze = item["title"]

        # Jika Saham Indo, TextBlob/VADER kurang akurat untuk Bhs Indo tanpa translate.
        # Tapi kita biarkan raw score dulu, nanti LLM yang 'reading' sebenarnya.
        score = analyze_sentiment_vader(text_to_analyze)

        item["sentiment_score"] = score
        processed_news.append(item)

    return processed_news


def analyze_news_sentiment(symbol, news_list):
    """
    Menganalisis list berita menjadi satu kesimpulan Sentimen (Bullish/Bearish).
    """
    if not news_list:
        return 0, "No News"

    total_score = 0
    headlines = []

    for n in news_list:
        total_score += n["sentiment_score"]
        headlines.append(n["title"])

    avg_score = total_score / len(news_list)

    # Buat Ringkasan String
    summary = f"Top Headlines: {headlines[0]}"
    if len(headlines) > 1:
        summary += f" | {headlines[1]}"

    # Mapping Score ke Kategori
    # > 0.2 : Bullish
    # < -0.2 : Bearish
    # -0.2 s/d 0.2 : Neutral

    final_sentiment = 0  # Netral
    if avg_score > 0.2:
        final_sentiment = 1  # Bullish
    if avg_score < -0.2:
        final_sentiment = -1  # Bearish

    return final_sentiment, summary
