import asyncio

import ccxt.async_support as ccxt
import pandas as pd
import yfinance as yf

from src.core.logger import logger
from src.feature.feature_enginering import enrich_data

# Daftar Exchange yang akan dicek (Urutan Prioritas)
# Gate & MEXC biasanya punya banyak koin micin/baru
EXCHANGE_LIST = [
    "binance",
    "bybit",
    "gateio",
    "mexc",
    "okx",
    "kucoin",
    "bingx",
    "bit2c",
    "bitbank",
    "bitbns",
    "bitflyer",
    "bitget",
]


async def fetch_crypto_ohlcv(symbol, timeframe="1h", limit=1000):
    """
    Multi-Exchange Fetcher: Mencari data di berbagai exchange secara bersamaan.
    """

    async def _close_exchange(exchange):
        if not exchange:
            return
        try:
            await exchange.close()
        except Exception:
            pass
        # Extra safety for some exchanges/aiohttp sessions
        session = getattr(exchange, "session", None)
        if session:
            try:
                await session.close()
            except Exception:
                pass

        # Explicitly try to close any internal connections if left open
        try:
            if hasattr(exchange, "clients"):
                for client in exchange.clients.values():
                    await client.close()
        except Exception:
            pass

    async def fetch_from_exchange(ex_name):
        exchange = None
        try:
            exchange_class = getattr(ccxt, ex_name)
            # enableRateLimit wajib agar tidak kena ban IP
            exchange = exchange_class({"enableRateLimit": True})

            # Fetch OHLCV
            ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

            if ohlcv and len(ohlcv) > 0:
                logger.info(
                    "✅ Found %s on %s (%d candles)", symbol, ex_name.upper(), len(ohlcv)
                )

                # Convert ke DataFrame
                cols: list = ["timestamp", "Open", "High", "Low", "Close", "Volume"]
                df = pd.DataFrame(ohlcv, columns=cols)
                df["Date"] = pd.to_datetime(df["timestamp"], unit="ms")
                df.set_index("Date", inplace=True)
                del df["timestamp"]

                return df, exchange

        except asyncio.CancelledError:
            pass
        except Exception:
            # Ignore error (misal symbol not found)
            pass

        await _close_exchange(exchange)
        return None, None

    tasks = [
        asyncio.create_task(fetch_from_exchange(ex_name))
        for ex_name in EXCHANGE_LIST
    ]

    result_df = pd.DataFrame()
    exchange_to_close = None

    pending = set(tasks)

    while pending:
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)

        for task in done:
            try:
                df, exchange = await task
                if df is not None:
                    if result_df.empty:
                        # First successful result
                        result_df = df
                        exchange_to_close = exchange
                        # Cancel remaining tasks
                        for t in pending:
                            t.cancel()
                    else:
                        # If multiple tasks completed at the exact same time, close the extra ones
                        await _close_exchange(exchange)
            except Exception:
                pass

        if not result_df.empty:
            break

    # Wait for cancelled tasks to handle CancelledError and close exchanges
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)

    if exchange_to_close:
        await _close_exchange(exchange_to_close)

    # Some exchanges require extra time to close resources in aiohttp
    await asyncio.sleep(0.1)

    if result_df.empty:
        logger.warning("❌ %s not found on any configured exchanges.", symbol)

    return result_df


def _fetch_yfinance_sync(symbol, period, interval):
    """Worker YFinance Synchronous"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval, auto_adjust=False)
        if df.empty and period == "2y":
            df = ticker.history(period="max", interval=interval, auto_adjust=False)
        return df
    except Exception as e:
        logger.error("YF Error %s: %s", symbol, e)
        return pd.DataFrame()


async def fetch_data_async(symbol, period="2y", interval="1h"):
    """
    Smart Data Fetcher (Async): Otomatis pilih YFinance atau CCXT Multi-Exchange.
    """
    df = pd.DataFrame()

    # 1. Deteksi Tipe Aset (Crypto pakai CCXT)
    # Ciri: Ada tanda '/' atau nama mengandung angka (1000PEPE)
    is_crypto = "/" in symbol

    if is_crypto:
        # Konversi Period '2y' ke Limit Candle (Estimasi)
        limit = 2000
        if period == "1mo":
            limit = 750

        df = await fetch_crypto_ohlcv(symbol, timeframe=interval, limit=limit)
    else:
        # Saham/Forex pakai YFinance
        df = await asyncio.to_thread(_fetch_yfinance_sync, symbol, period, interval)

    # 2. Validasi & Cleaning Data
    if df.empty:
        return df

    # Remove timezone information if present
    try:
        # Convert index to timezone-naive if it has timezone info
        if isinstance(df.index, pd.DatetimeIndex) and df.index.tz is not None:
            df = df.copy()
            # Create a new timezone-naive DatetimeIndex
            df.index = pd.to_datetime(df.index).tz_localize(None)
    except Exception:
        # Fallback for any errors during timezone conversion
        pass

    # Fix Kolom YFinance
    if "Adj Close" in df.columns:
        df = df.drop(columns=["Close"], errors="ignore")
        df = df.rename(columns={"Adj Close": "Close"})

    df = df.rename(columns={"Stock Splits": "Splits"})

    # Validasi Kolom Wajib
    required = ["Open", "High", "Low", "Close", "Volume"]
    for col in required:
        if col not in df.columns:
            if col == "Volume":
                df["Volume"] = 0
            else:
                return pd.DataFrame()

    # 3. Indikator Teknikal
    try:
        df_clean = enrich_data(df)

        return df_clean

    except Exception as e:
        logger.error("Indicator Error %s: %s", symbol, e)
        return pd.DataFrame()


# Wrapper Sync
def fetch_data(symbol, period="2y", interval="1h"):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(fetch_data_async(symbol, period, interval))

    # Fallback: if called inside a running event loop, execute in a separate thread.
    # This prevents "asyncio.run() cannot be called from a running event loop".
    import concurrent.futures

    def _runner():
        return asyncio.run(fetch_data_async(symbol, period, interval))

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_runner)
        return future.result()


def load_historical_data(symbol, period="2y", interval="1h"):
    """
    Load historical data (wrapper for fetch_data).
    """
    df = fetch_data(symbol, period, interval)
    return df
