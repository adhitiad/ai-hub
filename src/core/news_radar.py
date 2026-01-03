import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# Setup Logger jika belum ada
logger = logging.getLogger("backend")


def get_forex_calendar():
    """
    Scraping data Real-Time dari widget Investing.com (Forex Pros Tools).
    Menggantikan logika PHP simple_html_dom.
    """
    url = "https://sslecal2.forexprostools.com/"

    # Headers penting agar tidak diblokir sebagai bot
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            logger.error(f"Failed to fetch calendar. Status: {response.status_code}")
            return []

        soup = BeautifulSoup(response.content, "lxml")  # Parser cepat

        # Selektor CSS: Cari tabel dengan ID ecEventsTable
        table = soup.find("table", id="ecEventsTable")
        if not table:
            return []

        # Cari semua baris (tr) yang ID-nya mengandung 'eventRowId'
        # PHP: $dom->getElementById("#ecEventsTable")->find("tr[id*='eventRowId']")
        rows = table.find_all("tr", id=lambda x: x and "eventRowId" in x)

        data = []

        for row in rows:
            # 1. Ambil Timestamp (dari atribut event_timestamp)
            # Format asli: "2024-05-21 14:30:00"
            raw_timestamp = row.get("event_timestamp", "")
            time_display = ""

            try:
                # Kita ubah jadi HH:MM saja untuk display
                dt_obj = datetime.strptime(raw_timestamp, "%Y-%m-%d %H:%M:%S")
                time_display = dt_obj.strftime("%H:%M")
            except:
                time_display = raw_timestamp

            # 2. Ambil Currency (PHP: td.flagCur)
            currency_cell = row.select_one("td.flagCur")
            currency = (
                currency_cell.get_text(strip=True).replace("\u00a0", "")
                if currency_cell
                else ""
            )

            # 3. Ambil Impact (PHP: hitung i.grayFullBullishIcon)
            # Logika Investing: 1 Bull = Low, 2 Bull = Medium, 3 Bull = High
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

            # 4. Ambil Nama Event (PHP: td.event)
            event_cell = row.select_one("td.event")
            event_name = (
                event_cell.get_text(strip=True) if event_cell else "Unknown Event"
            )

            # 5. Data Angka (Actual, Forecast, Previous)
            actual = (
                row.select_one("td.act").get_text(strip=True)
                if row.select_one("td.act")
                else ""
            )
            forecast = (
                row.select_one("td.fore").get_text(strip=True)
                if row.select_one("td.fore")
                else ""
            )
            prev = (
                row.select_one("td.prev").get_text(strip=True)
                if row.select_one("td.prev")
                else ""
            )

            # Filter HANYA berita High/Medium Impact (Opsional, agar dashboard tidak penuh)
            # Jika ingin semua, hapus if ini.
            if impact_str in ["HIGH", "MEDIUM"]:
                data.append(
                    {
                        "time": time_display,  # "19:30"
                        "currency": currency,  # "USD"
                        "event": event_name,  # "Non-Farm Payrolls"
                        "impact": impact_str,  # "HIGH"
                        "actual": actual,
                        "forecast": forecast,
                        "previous": prev,
                        "raw_datetime": raw_timestamp,  # Disimpan untuk keperluan sorting nanti
                    }
                )

        return data

    except Exception as e:
        logger.error(f"Error scraping news: {e}")
        return []


# Fungsi wrapper agar kompatibel dengan kode yang sudah ada
def get_high_impact_news():
    return get_forex_calendar()
