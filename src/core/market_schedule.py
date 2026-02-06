from datetime import datetime

import pytz

# Tambahkan Enum atau Konstanta
ASSET_TYPES = ["STOCK", "CRYPTO", "FOREX"]


def is_market_open(asset_type: str) -> bool:
    """Check if market is open for the given asset type."""
    now = datetime.now(pytz.utc)

    # 1. CRYPTO: Buka 24/7
    if asset_type == "CRYPTO":
        return True

    # 2. FOREX: Buka 24/5 (Tutup Sabtu-Minggu)
    if asset_type == "FOREX":
        return now.weekday() < 5  # 0=Senin, 4=Jumat. 5&6 Libur.

    # 3. STOCK (IHSG): Logic Lama (09:00 - 16:00 WIB)
    # Asumsi server UTC, WIB = UTC+7
    wib_hour = (now.hour + 7) % 24
    is_weekday = now.weekday() < 5
    # Sederhana: Buka jam 9 pagi sampai 4 sore WIB
    return is_weekday and (9 <= wib_hour < 16)


class MarketSchedule:
    def is_market_open(self, asset_type: str) -> bool:
        """Check if market is open for the given asset type."""
        return is_market_open(asset_type)


market_schedule = MarketSchedule()
