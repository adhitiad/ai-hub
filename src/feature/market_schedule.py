from datetime import datetime, time

import pytz

JAKARTA_TZ = pytz.timezone("Asia/Jakarta")

# Tambahkan Enum atau Konstanta
ASSET_TYPES = ["STOCK", "CRYPTO", "FOREX", "STOCKS_INDO"]


def _is_forex_open(now) -> bool:
    if now.weekday() >= 5:
        return False
    # Rollover window (sekitar 05:00 UTC) dianggap tutup
    if now.hour == 5:
        return False
    return True


def _is_indo_stocks_open(now) -> bool:
    if now.weekday() >= 5:
        return False

    current_time = now.time()

    # Jam bursa (sederhana) dengan pre-opening
    if now.weekday() == 4:  # Jumat
        return (time(8, 45) <= current_time < time(11, 30)) or (
            time(14, 0) <= current_time < time(15, 50)
        )

    return (time(8, 45) <= current_time < time(12, 0)) or (
        time(13, 30) <= current_time < time(15, 50)
    )


def is_market_open(asset_type: str) -> bool:
    """Check if market is open for the given asset type."""
    now = datetime.now(JAKARTA_TZ)

    # 1. CRYPTO: Buka 24/7
    if asset_type == "CRYPTO":
        return True

    # 2. FOREX: Buka 24/5 (Tutup Sabtu-Minggu + rollover)
    if asset_type == "FOREX":
        return _is_forex_open(now)

    # 3. STOCK (IHSG)
    if asset_type in {"STOCK", "STOCKS_INDO", "IHSG"}:
        return _is_indo_stocks_open(now)

    # Default: buka (fallback)
    return True


class MarketSchedule:
    def is_market_open(self, asset_type: str) -> bool:
        """Check if market is open for the given asset type."""
        return is_market_open(asset_type)


market_schedule = MarketSchedule()
