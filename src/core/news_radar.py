import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from src.core.logger import logger
from src.core.news_collector import analyze_sentiment_vader, get_google_news_rss


class NewsRadar:
    def __init__(self):
        # Penyimpanan Cache Data
        self._cache_data = []
        self._last_update = 0
        self._cache_duration = 600  # 600 detik = 10 menit (Agar tidak kena blokir)

    def _scrape_forex_factory(self):
        """
        Scraping data Real-Time dari widget Investing.com.
        """
        url = "https://sslecal2.forexprostools.com/"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

        try:
            logger.info("📡 Scraping Economic Calendar...")
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code != 200:
                logger.error(
                    f"Failed to fetch calendar. Status: {response.status_code}"
                )
                return []

            soup = BeautifulSoup(response.content, "lxml")

            table = soup.find("table", id="ecEventsTable")
            if not table:
                return []

            all_rows = table.find_all("tr")
            rows = [
                row
                for row in all_rows
                if row.get("id") and "eventRowId" in str(row.get("id", ""))
            ]

            data = []

            for row in rows:
                # 1. Timestamp
                raw_timestamp = row.get("event_timestamp", "")
                time_display = ""
                try:
                    if isinstance(raw_timestamp, str) and raw_timestamp:
                        dt_obj = datetime.strptime(raw_timestamp, "%Y-%m-%d %H:%M:%S")
                        time_display = dt_obj.strftime("%H:%M")
                    else:
                        time_display = str(raw_timestamp)
                except:
                    time_display = str(raw_timestamp)

                # 2. Currency
                currency_cell = row.select_one("td.flagCur")
                currency = (
                    currency_cell.get_text(strip=True).replace("\u00a0", "")
                    if currency_cell
                    else ""
                )

                # 3. Impact
                sentiment_cell = row.select_one("td.sentiment")
                bulls_count = (
                    len(sentiment_cell.select("i.grayFullBullishIcon"))
                    if sentiment_cell
                    else 0
                )

                impact_str = "LOW"
                if bulls_count == 2:
                    impact_str = "MEDIUM"
                if bulls_count == 3:
                    impact_str = "HIGH"

                # 4. Event Name
                event_cell = row.select_one("td.event")
                event_name = (
                    event_cell.get_text(strip=True) if event_cell else "Unknown Event"
                )

                # 5. Data Angka
                actual_cell = row.select_one("td.act")
                actual = actual_cell.get_text(strip=True) if actual_cell else ""
                forecast_cell = row.select_one("td.fore")
                forecast = forecast_cell.get_text(strip=True) if forecast_cell else ""
                prev_cell = row.select_one("td.prev")
                prev = prev_cell.get_text(strip=True) if prev_cell else ""

                # Filter Impact
                if impact_str in ["HIGH", "MEDIUM"]:
                    data.append(
                        {
                            "time": time_display,
                            "currency": currency,
                            "event": event_name,
                            "impact": impact_str,
                            "actual": actual,
                            "forecast": forecast,
                            "previous": prev,
                            "raw_datetime": raw_timestamp,
                        }
                    )

            logger.info(f"✅ Scraped {len(data)} events successfully.")
            return data

        except Exception as e:
            logger.error(f"❌ Error scraping news: {e}")
            return []

    def get_upcoming_events(self, limit=10):
        """
        Mengembalikan data berita.
        Menggunakan Cache jika request dilakukan < 10 menit yang lalu.
        """
        current_time = time.time()

        # Cek Cache
        if self._cache_data and (
            current_time - self._last_update < self._cache_duration
        ):
            # logger.info("Using Cached News Data")
            return self._cache_data[:limit]

        # Jika Cache Expired atau Kosong, Scrape ulang
        new_data = self._scrape_forex_factory()

        if new_data:
            self._cache_data = new_data
            self._last_update = current_time
            return new_data[:limit]
        else:
            logger.warning("No new data found, using cached data.")
            return self._cache_data[:limit] if self._cache_data else []

    def check_global_panic(self):
        """
        Mengecek apakah ada kepanikan global di berita.
        Menggunakan keyword sensitif di Google News.
        """
        panic_keywords = [
            "Market Crash",
            "Recession",
            "War",
            "Inflation Spike",
            "Pandemic",
        ]

        # Search query gabungan
        query = "OR".join(panic_keywords)
        news = get_google_news_rss(query, asset_type="forex")  # Pakai mode global (US)

        negative_count = 0
        for n in news:
            if analyze_sentiment_vader(n["title"]) < -0.3:  # Sangat negatif
                negative_count += 1

        # Jika 3 dari 5 berita teratas sangat negatif tentang "Crash/War"
        if negative_count >= 3:
            return True, "🚨 GLOBAL PANIC NEWS DETECTED"

        return False, "Stable"

    async def get_sentiment(self, symbol: str) -> str:
        """
        Get sentiment analysis for a specific symbol.
        Placeholder implementation.
        """
        # For now, return a simple sentiment analysis
        return f"Neutral sentiment for {symbol}. No recent news available."


# Singleton Instance
news_radar = NewsRadar()
