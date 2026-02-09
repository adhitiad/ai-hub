import numpy as np
import pandas as pd
import pandas_ta as ta

from src.core.logger import logger

# --- DEFINISI FITUR BAKU ---
# Digunakan untuk memastikan urutan kolom sama saat Training vs Live
FEATURE_COLUMNS = [
    "RSI_14",
    "MACD_12_26_9",
    "MACDh_12_26_9",
    "ATR_14",
    "dist_sma20",
    "dist_sma50",
    "Volume_Norm",
]


def enrich_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Menambahkan indikator teknikal ke DataFrame mentah (OHLCV).
    """
    if df.empty:
        return df

    df = df.copy()

    # Validasi kolom wajib
    required = ["Close", "Volume"]
    if not all(col in df.columns for col in required):
        logger.warning(f"❌ Missing required columns for features: {df.columns}")
        return df

    try:
        # 1. Indikator Library (Pandas TA)
        # Append=True otomatis menambahkan kolom ke df
        df.ta.rsi(length=14, append=True)
        df.ta.macd(fast=12, slow=26, signal=9, append=True)
        df.ta.sma(length=20, append=True)
        df.ta.sma(length=50, append=True)
        df.ta.atr(length=14, append=True)

        # 2. Custom Feature Engineering
        # Jarak harga ke SMA (Trend Strength)
        if "SMA_20" in df.columns:
            df["dist_sma20"] = (df["Close"] - df["SMA_20"]) / df["SMA_20"]
        else:
            df["dist_sma20"] = 0

        if "SMA_50" in df.columns:
            df["dist_sma50"] = (df["Close"] - df["SMA_50"]) / df["SMA_50"]
        else:
            df["dist_sma50"] = 0

        # Normalisasi Volume
        vol_mean = df["Volume"].rolling(window=20).mean()
        df["Volume_Norm"] = df["Volume"] / (vol_mean + 1e-9)

        # 3. Handling NaN
        # Forward fill dulu, lalu isi 0 untuk sisa (awal data)
        df.ffill(inplace=True)
        df.fillna(0, inplace=True)

    except Exception as e:
        logger.error(f"⚠️ Feature Engineering Error: {e}")

    return df


def get_model_input(df: pd.DataFrame) -> pd.DataFrame:
    """Filter hanya kolom fitur untuk input Model AI"""
    # Pastikan semua kolom fitur ada
    for col in FEATURE_COLUMNS:
        if col not in df.columns:
            df[col] = 0.0

    return df[FEATURE_COLUMNS]
