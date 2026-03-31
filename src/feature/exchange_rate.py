import yfinance as yf
import time
import asyncio
from src.core.logger import logger
import traceback

# Cache to store exchange rates
# Format: { "QUOTE": {"rate": float, "timestamp": int} }
_RATE_CACHE = {}
_CACHE_TTL = 3600  # 1 hour in seconds


async def get_usd_conversion_rate(quote_currency: str) -> float:
    """
    Get the exchange rate to convert 1 unit of quote_currency into USD.
    Returns 1.0 if quote_currency is USD or if fetching fails.
    """
    if not quote_currency or quote_currency.upper() == "USD":
        return 1.0

    quote = quote_currency.upper()
    now = time.time()

    # Check cache
    if quote in _RATE_CACHE:
        cache_entry = _RATE_CACHE[quote]
        if now - cache_entry["timestamp"] < _CACHE_TTL:
            return cache_entry["rate"]

    def _fetch_yf_history(sym):
        return yf.Ticker(sym).history(period="1d")

    # Try fetching the rate from yfinance
    try:
        # First try QUOTEUSD=X (e.g. GBPUSD=X -> 1 GBP = X USD)
        symbol = f"{quote}USD=X"
        df = await asyncio.to_thread(_fetch_yf_history, symbol)
        if not df.empty and not df["Close"].isna().all():
            rate = float(df["Close"].iloc[-1])
            if rate > 0:
                _RATE_CACHE[quote] = {"rate": rate, "timestamp": now}
                logger.info(f"Fetched exchange rate {symbol}: {rate}")
                return rate

        # If that fails, try QUOTE=X (Usually USDQUOTE=X -> 1 USD = X QUOTE)
        symbol2 = f"{quote}=X"
        df2 = await asyncio.to_thread(_fetch_yf_history, symbol2)
        if not df2.empty and not df2["Close"].isna().all():
            usd_per_quote_rate = float(df2["Close"].iloc[-1])
            if usd_per_quote_rate > 0:
                rate = 1.0 / usd_per_quote_rate
                _RATE_CACHE[quote] = {"rate": rate, "timestamp": now}
                logger.info(
                    f"Fetched exchange rate {symbol2}: {usd_per_quote_rate} -> 1 {quote} = {rate} USD"
                )
                return rate

    except Exception as e:
        logger.error(f"Failed to fetch exchange rate for {quote}: {e}")
        # traceback.print_exc()

    # If all fails, return 1.0 as a fallback
    return 1.0

    quote = quote_currency.upper()
    now = time.time()

    # Check cache
    if quote in _RATE_CACHE:
        cache_entry = _RATE_CACHE[quote]
        if now - cache_entry["timestamp"] < _CACHE_TTL:
            return cache_entry["rate"]

    # Try fetching the rate from yfinance
    try:
        # First try QUOTEUSD=X (e.g. GBPUSD=X -> 1 GBP = X USD)
        symbol = f"{quote}USD=X"
        df = yf.Ticker(symbol).history(period="1d")
        if not df.empty and not df["Close"].isna().all():
            rate = float(df["Close"].iloc[-1])
            if rate > 0:
                _RATE_CACHE[quote] = {"rate": rate, "timestamp": now}
                logger.info(f"Fetched exchange rate {symbol}: {rate}")
                return rate

        # If that fails, try QUOTE=X (Usually USDQUOTE=X -> 1 USD = X QUOTE)
        symbol2 = f"{quote}=X"
        df2 = yf.Ticker(symbol2).history(period="1d")
        if not df2.empty and not df2["Close"].isna().all():
            usd_per_quote_rate = float(df2["Close"].iloc[-1])
            if usd_per_quote_rate > 0:
                rate = 1.0 / usd_per_quote_rate
                _RATE_CACHE[quote] = {"rate": rate, "timestamp": now}
                logger.info(
                    f"Fetched exchange rate {symbol2}: {usd_per_quote_rate} -> 1 {quote} = {rate} USD"
                )
                return rate

    except Exception as e:
        logger.error(f"Failed to fetch exchange rate for {quote}: {e}")
        # traceback.print_exc()

    # If all fails, return 1.0 as a fallback
    return 1.0


def extract_quote_currency(symbol: str) -> str:
    """
    Extract quote currency from typical Yahoo Finance forex/crypto symbols.
    Examples: EURGBP=X -> GBP, EURUSD=X -> USD, JPY=X -> JPY, BTC-USD -> USD
    """
    if symbol.endswith("=X"):
        # E.g., EURGBP=X -> EUR (base), GBP (quote)
        # JPY=X -> USD (base, implicit), JPY (quote)
        base_quote = symbol[:-2]
        if len(base_quote) == 6:
            return base_quote[3:]
        elif len(base_quote) == 3:
            return base_quote  # e.g. JPY
    elif "-" in symbol:
        # e.g., BTC-USD
        parts = symbol.split("-")
        if len(parts) == 2:
            return parts[1]

    return "USD"  # default
