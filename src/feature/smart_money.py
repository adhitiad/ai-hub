import numpy as np
import pandas as pd


def analyze_forex_whale(df):
    """
    Core Logic: Mendeteksi jejak Institutional Trader (SMC)
    """
    if len(df) < 50:
        return {"detected": False, "score": 0, "type": "NEUTRAL", "strength": "LOW"}

    # Data Data Terakhir
    curr = df.iloc[-1]

    # 1. Hitung ATR (Volatilitas) & Volume Rata-rata
    atr = df["ATR_14"].iloc[-1] if "ATR_14" in df.columns else 0
    avg_vol = df["Volume"].rolling(20).mean().iloc[-1]
    curr_vol = curr["Volume"]

    # Ukuran Candle (Body & Range)
    body_size = abs(curr["Close"] - curr["Open"])

    whale_signal = {
        "detected": False,
        "score": 0,  # Netral
        "type": "NEUTRAL",
        "message": "Market Normal",
        "strength": "LOW",
    }

    # Support/Resist lokal (Low/High 15 candle terakhir)
    recent_low = df["Low"].iloc[-15:-1].min()
    recent_high = df["High"].iloc[-15:-1].max()

    # --- LOGIC 1: LIQUIDITY GRAB (STOP HUNT) ---

    # DETEKSI BULLISH WHALE (Bear Trap / Liquidity Grab Lower)
    if (curr["Low"] < recent_low) and (curr["Close"] > recent_low):
        if curr_vol > (avg_vol * 1.2):
            whale_signal = {
                "detected": True,
                "score": 25,  # Menambah skor BUY
                "type": "WHALE_BUY",
                "message": "⚠️ SMC: Liquidity Grab (Bear Trap) Detected",
                "strength": "HIGH",
            }

    # DETEKSI BEARISH WHALE (Bull Trap / Liquidity Grab Upper)
    elif (curr["High"] > recent_high) and (curr["Close"] < recent_high):
        if curr_vol > (avg_vol * 1.2):
            whale_signal = {
                "detected": True,
                "score": -25,  # Mengurangi skor (Signal SELL)
                "type": "WHALE_SELL",
                "message": "⚠️ SMC: Liquidity Grab (Bull Trap) Detected",
                "strength": "HIGH",
            }

    # --- LOGIC 2: MOMENTUM IMBALANCE ---

    elif body_size > (atr * 2.0):
        if curr["Close"] > curr["Open"]:
            whale_signal = {
                "detected": True,
                "score": 15,
                "type": "MOMENTUM_BUY",
                "message": "Institutional Buying (Imbalance)",
                "strength": "MEDIUM",
            }
        else:
            whale_signal = {
                "detected": True,
                "score": -15,
                "type": "MOMENTUM_SELL",
                "message": "Institutional Selling (Imbalance)",
                "strength": "MEDIUM",
            }

    return whale_signal


def analyze_smart_money(df):
    """
    Wrapper function agar nama fungsi konsisten dengan import di scoring.py
    """
    return analyze_forex_whale(df)
