import asyncio

import ccxt.async_support as ccxt
import pandas as pd
import pandas_ta as ta
import yfinance as yf

from src.core.feature_enginering import enrich_data, get_model_input
from src.core.logger import logger

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
    Multi-Exchange Fetcher: Mencari data di berbagai exchange secara berurutan.
    """
    for ex_name in EXCHANGE_LIST:
        exchange_class = getattr(ccxt, ex_name)
        # enableRateLimit wajib agar tidak kena ban IP
        exchange = exchange_class({"enableRateLimit": True})

        try:
            # logger.info(f"🔍 Checking {symbol} on {ex_name.upper()}...")

            # Fetch OHLCV
            ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

            if ohlcv and len(ohlcv) > 0:
                print(f"✅ Found {symbol} on {ex_name.upper()} ({len(ohlcv)} candles)")

                # Convert ke DataFrame
                df = pd.DataFrame(
                    ohlcv,
                    columns=["timestamp", "Open", "High", "Low", "Close", "Volume"],
                )
                df["Date"] = pd.to_datetime(df["timestamp"], unit="ms")
                df.set_index("Date", inplace=True)
                del df["timestamp"]

                await exchange.close()
                return df

        except Exception:
            # Ignore error (misal symbol not found), lanjut ke exchange berikutnya
            pass
        finally:
            await exchange.close()

    # Jika sudah cek semua exchange tapi nihil
    print(f"❌ {symbol} not found on any configured exchanges.")
    return pd.DataFrame()


def _fetch_yfinance_sync(symbol, period, interval):
    """Worker YFinance Synchronous"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval, auto_adjust=False)
        if df.empty and period == "2y":
            df = ticker.history(period="max", interval=interval, auto_adjust=False)
        return df
    except Exception as e:
        logger.error(f"YF Error {symbol}: {e}")
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
        logger.error(f"Indicator Error {symbol}: {e}")
        return pd.DataFrame()


# Wrapper Sync
def fetch_data(symbol, period="2y", interval="1h"):
    return asyncio.run(fetch_data_async(symbol, period, interval))
