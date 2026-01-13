import numpy as np
import pandas as pd
import pandas_ta as ta
from sklearn.preprocessing import StandardScaler

# --- DEFINISI FITUR BAKU (JANGAN UBAH URUTANNYA!) ---
# Urutan ini harus SAMA PERSIS untuk Training (RF/PPO) dan Live Trading.
FEATURE_COLUMNS = [
    "RSI_14",
    "MACD_12_26_9",
    "MACDh_12_26_9",  # Histogram MACD
    "ATR_14",
    "dist_sma20",
    "dist_sma50",
    "Volume_Norm",  # Volume yang dinormalisasi sederhana
]


def enrich_data(df):
    """
    Menambahkan indikator teknikal ke DataFrame mentah (OHLCV).
    Digunakan oleh: data_loader, train_rf, env, dan live producer.
    """
    df = df.copy()

    # Pastikan kolom dasar ada
    required = ["Close", "Volume"]
    if not all(col in df.columns for col in required):
        return df

    # 1. Hitung Indikator Dasar (Pandas TA)
    # Gunakan try-except agar tidak crash jika data terlalu sedikit
    try:
        df.ta.rsi(length=14, append=True)
        df.ta.macd(fast=12, slow=26, signal=9, append=True)
        df.ta.sma(length=20, append=True)
        df.ta.sma(length=50, append=True)
        df.ta.atr(length=14, append=True)
    except Exception:
        pass

    # 2. Feature Engineering (Custom)
    # Jarak harga ke SMA (Trend Strength)
    if "SMA_20" in df.columns:
        df["dist_sma20"] = (df["Close"] - df["SMA_20"]) / df["SMA_20"]
    else:
        df["dist_sma20"] = 0

    if "SMA_50" in df.columns:
        df["dist_sma50"] = (df["Close"] - df["SMA_50"]) / df["SMA_50"]
    else:
        df["dist_sma50"] = 0

    # Normalisasi Volume sederhana (dibagi rata-rata volume)
    # Agar angkanya tidak jutaan vs RSI yang cuma 0-100
    vol_mean = df["Volume"].rolling(window=20).mean()
    df["Volume_Norm"] = df["Volume"] / (vol_mean + 1e-9)

    # Isi NaN (akibat windowing) dengan 0 atau drop nanti
    df = df.fillna(0)

    return df


def get_model_input(df):
    """
    Hanya mengambil kolom fitur yang didefinisikan di FEATURE_COLUMNS.
    Memastikan urutan kolom SELALU SAMA.
    """
    # Pastikan semua kolom ada, jika tidak, isi dengan 0
    for col in FEATURE_COLUMNS:
        if col not in df.columns:
            df[col] = 0.0

    # Return hanya kolom fitur (X)
    return df[FEATURE_COLUMNS]
