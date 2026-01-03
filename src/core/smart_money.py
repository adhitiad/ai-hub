import numpy as np
import pandas as pd


def analyze_forex_whale(df):
    """
    Mendeteksi jejak Institutional Trader di Forex menggunakan konsep SMC
    (Liquidity Grabs & Imbalance).
    """
    if len(df) < 50:
        return None

    # Data Data Terakhir
    curr = df.iloc[-1]
    prev = df.iloc[-2]

    # 1. Hitung ATR (Volatilitas) & Volume Rata-rata
    atr = df["ATR_14"].iloc[-1]
    avg_vol = df["Volume"].rolling(20).mean().iloc[-1]
    curr_vol = curr["Volume"]

    # Ukuran Candle (Body & Range)
    body_size = abs(curr["Close"] - curr["Open"])
    total_range = curr["High"] - curr["Low"]

    whale_signal = {
        "detected": False,
        "type": "NEUTRAL",
        "message": "Market Normal",
        "strength": "LOW",
    }

    # --- LOGIC 1: LIQUIDITY GRAB (STOP HUNT) ---
    # Ciri: Ekor panjang menembus support/resist, tapi close balik arah
    # Ini tanda Bank sedang 'belanja' Stop Loss ritel.

    # Cari Support/Resistance lokal (Low/High 10 candle terakhir)
    recent_low = df["Low"].iloc[-15:-1].min()
    recent_high = df["High"].iloc[-15:-1].max()

    # DETEKSI BULLISH WHALE (Bear Trap)
    # Harga sempat turun di bawah Low terendah (Breakout palsu),
    # lalu Close kembali di atasnya dengan Volume tinggi.
    if (curr["Low"] < recent_low) and (curr["Close"] > recent_low):
        if curr_vol > (avg_vol * 1.5):  # Volume minimal 1.5x rata-rata
            whale_signal = {
                "detected": True,
                "type": "WHALE_BUY",
                "message": "Liquidity Grab Detected (Bear Trap)",
                "strength": "HIGH",
            }

    # DETEKSI BEARISH WHALE (Bull Trap)
    # Harga sempat naik di atas High tertinggi,
    # lalu Close kembali di bawahnya.
    elif (curr["High"] > recent_high) and (curr["Close"] < recent_high):
        if curr_vol > (avg_vol * 1.5):
            whale_signal = {
                "detected": True,
                "type": "WHALE_SELL",
                "message": "Liquidity Grab Detected (Bull Trap)",
                "strength": "HIGH",
            }

    # --- LOGIC 2: INSTITUTIONAL CANDLE (IMBALANCE) ---
    # Ciri: Candle sangat besar (Marubozu) searah trend
    # Ini tanda Bank masuk uang besar (Momentum).

    elif body_size > (atr * 2.0):  # Body candle 2x lipat rata-rata harian
        if curr["Close"] > curr["Open"]:
            whale_signal = {
                "detected": True,
                "type": "MOMENTUM_BUY",
                "message": "Institutional Buying Pressure (Imbalance)",
                "strength": "MEDIUM",
            }
        else:
            whale_signal = {
                "detected": True,
                "type": "MOMENTUM_SELL",
                "message": "Institutional Selling Pressure (Imbalance)",
                "strength": "MEDIUM",
            }

    return whale_signal
