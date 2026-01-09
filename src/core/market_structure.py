import numpy as np
import pandas as pd

from src.core.data_loader import fetch_data
from src.core.logger import logger


def check_mtf_trend(symbol, current_tf="1h"):
    """
    Dynamic Multi-Timeframe (MTF) Confirmation.
    Mengecek tren di Timeframe 'Kakak Kelas'-nya.

    Mapping:
    - 1h (H1) -> Cek 4h (H4)
    - 15m (M15) -> Cek 1h (H1)
    - 1d (D1) -> Cek 1wk (Weekly)
    """
    # 1. Tentukan Timeframe Atas
    tf_map = {
        "15m": "1h",
        "1h": "1d",  # Data H4 di yfinance kadang tidak stabil, aman ke D1
        "1d": "1wk",
    }

    higher_tf = tf_map.get(current_tf)
    if not higher_tf:
        return "NEUTRAL", "No MTF Config"

    try:
        # 2. Ambil Data Timeframe Atas
        # Kita butuh data cukup untuk hitung EMA 200
        df_high = fetch_data(symbol, period="2y", interval=higher_tf)

        if df_high.empty:
            return "NEUTRAL", "MTF Data Empty"

        # 3. Analisis Trend (EMA 200)
        # Menggunakan pandas-ta yang sudah di-load di fetch_data atau manual
        # Di fetch_data standard Anda mungkin belum ada EMA 200, kita hitung manual cepat
        close_prices = df_high["Close"]
        ema_200 = close_prices.ewm(span=200, adjust=False).mean().iloc[-1]
        current_price = close_prices.iloc[-1]

        # Analisis Slope (Kemiringan) EMA 50 untuk trend jangka menengah
        ema_50 = close_prices.ewm(span=50, adjust=False).mean()
        slope = ema_50.iloc[-1] - ema_50.iloc[-5]  # Perubahan 5 candle terakhir

        status = "SIDEWAYS"

        if current_price > ema_200:
            if slope > 0:
                status = "UPTREND"
            else:
                status = "WEAK_UPTREND"
        else:
            if slope < 0:
                status = "DOWNTREND"
            else:
                status = "WEAK_DOWNTREND"

        return status, f"Price vs EMA200 ({higher_tf}) is {status}"

    except Exception as e:
        logger.error(f"MTF Check Error {symbol}: {e}")
        return "NEUTRAL", "Error"


def detect_insider_volume(df):
    """
    Mendeteksi 'Insider' Anomaly (Volume Spike).
    Ciri: Volume meledak, tapi harga tidak bergerak banyak (dijaga/akumulasi diam-diam).
    """
    if df.empty or len(df) < 20:
        return False, "No Data"

    last = df.iloc[-1]

    # 1. Hitung Rata-rata Volume 20 candle terakhir
    avg_vol = df["Volume"].rolling(20).mean().iloc[-1]

    if avg_vol == 0:
        return False, ""

    # 2. Ratio Volume Hari Ini
    vol_ratio = last["Volume"] / avg_vol

    # 3. Perubahan Harga (Body Candle dalam Persen)
    open_price = last["Open"]
    close_price = last["Close"]
    price_change_pct = abs(close_price - open_price) / open_price * 100

    # --- LOGIKA INSIDER ---
    # Skenario 1: Volume Super Besar (> 5x rata-rata) TAPI Harga Kalem (< 0.5% move)
    # Ini indikasi "Churning" atau pertukaran barang antar bandar/insider di harga tetap.
    if vol_ratio > 5.0 and price_change_pct < 0.5:
        return (
            True,
            f"⚠️ INSIDER DETECTED: Volume {vol_ratio:.1f}x spike with flat price.",
        )

    # Skenario 2: Volume Besar (> 3x) di candle Doji
    is_doji = abs(close_price - open_price) <= (last["High"] - last["Low"]) * 0.1
    if vol_ratio > 3.0 and is_doji:
        return True, f"⚠️ ANOMALY: High Volatility Doji ({vol_ratio:.1f}x vol)."

    return False, "Normal"
