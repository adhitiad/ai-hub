# src/core/agent.py

import asyncio
import glob
import os

import numpy as np
import pandas as pd
from stable_baselines3 import PPO

# --- 2. ADVANCED ANALYSIS IMPORTS ---
from src.core.bandarmology import analyze_bandar_flow

# --- 1. CORE IMPORTS ---
from src.core.config_assets import get_asset_info
from src.core.data_loader import fetch_data
from src.core.market_structure import check_mtf_trend, detect_insider_volume
from src.core.money_management import (  # [OK] Wajib ada agar Unit Test @patch('src.core.agent.calculate_lot_size') berhasil
    calculate_kelly_lot,
    calculate_lot_size,
    check_correlation_risk,
)
from src.core.pattern_recognizer import detect_chart_patterns

# --- 3. RISK & MONEY MANAGEMENT ---
from src.core.risk_manager import check_circuit_breaker

# [OK] Vector DB Import
from src.core.vector_db import recall_similar_events

# --- 4. OPTIONAL MODULES (ML & News) ---
try:
    from src.core.ml_features import ml_analyzer
    from src.core.news_collector import analyze_news_sentiment, fetch_market_news
except ImportError:
    pass

MODEL_DIR = "models"


async def get_detailed_signal(symbol, asset_info, custom_balance=None):
    """
    ULTIMATE SIGNAL GENERATOR (Async Version)
    """
    try:
        # --- A. SETUP & VALIDATION ---
        if not asset_info:
            info = get_asset_info(symbol)
            if not info:
                return {
                    "Symbol": symbol,
                    "Action": "HOLD",
                    "Reason": "Asset not config.",
                }
        else:
            info = asset_info

        asset_type = info.get("type", "forex")
        category = info.get("category", "forex").lower()
        safe_symbol = symbol.replace("=", "").replace("^", "")

        # --- B. GLOBAL RISK CHECKS ---
        can_trade, reject_reason = await check_circuit_breaker()
        if not can_trade:
            return {
                "Symbol": symbol,
                "Action": "HOLD",
                "Reason": f"Risk: {reject_reason}",
            }

        is_uncorrelated, corr_msg = await check_correlation_risk(symbol)
        if not is_uncorrelated:
            return {"Symbol": symbol, "Action": "HOLD", "Reason": f"Risk: {corr_msg}"}

        # --- C. LOAD MODEL & DATA ---
        base_dir = f"{MODEL_DIR}/{category}"
        pattern = f"{base_dir}/{safe_symbol}*.zip"
        files = glob.glob(pattern)
        files.sort(reverse=True)

        if not files:
            return {"Symbol": symbol, "Action": "HOLD", "Reason": "No Model Trained"}

        df = fetch_data(symbol, period="2y", interval="1h")
        if df.empty:
            return {"Symbol": symbol, "Action": "HOLD", "Reason": "No Data"}

        model = PPO.load(files[0])

        # --- D. AI PREDICTION ---
        last_row = df.iloc[-1]
        obs = np.append(last_row.values, [0])
        action, _ = model.predict(obs)

        action_map = {0: "HOLD", 1: "BUY", 2: "SELL"}
        base_action = action_map[int(action)]

        confidence = 70.0
        reasons = []

        # --- E. ADVANCED ANALYSIS INTEGRATION ---

        # 1. VECTOR DB RECALL (History Check)
        # Mengecek apakah pola chart ini pernah terjadi sebelumnya dan hasilnya profit/loss
        history_outcome = recall_similar_events(df)
        if history_outcome == "WIN":
            confidence += 5
            reasons.append("History Match: Profitable Pattern 📜")
        elif history_outcome == "LOSS":
            confidence -= 10
            reasons.append("History Match: Bad Pattern 📜")

        # 2. MARKET STRUCTURE
        mtf_trend = check_mtf_trend(symbol, current_tf="1h")
        if base_action == "BUY":
            if mtf_trend == "UP":
                confidence += 10
                reasons.append("MTF Trend: Bullish ✅")
            elif mtf_trend == "DOWN":
                confidence -= 20
                reasons.append("MTF Trend: Bearish ⚠️")
        elif base_action == "SELL":
            if mtf_trend == "DOWN":
                confidence += 10
                reasons.append("MTF Trend: Bearish ✅")
            elif mtf_trend == "UP":
                confidence -= 20
                reasons.append("MTF Trend: Bullish ⚠️")

        # 3. INSIDER VOLUME
        if detect_insider_volume(df):
            confidence += 10
            reasons.append("Insider Volume Spike 🐳")

        # 4. BANDARMOLOGY
        bandar_result = analyze_bandar_flow(df)
        flow_status = bandar_result["status"]
        if base_action == "BUY" and "ACCUM" in flow_status:
            confidence += 15
            reasons.append("Bandar Accumulation 💰")
        elif base_action == "SELL" and "DISTRIB" in flow_status:
            confidence += 15
            reasons.append("Bandar Distribution 📉")

        # 5. CHART PATTERNS
        pattern_score, detected_patterns = detect_chart_patterns(df)
        if detected_patterns:
            reasons.append(f"Patterns: {', '.join(detected_patterns)}")
            confidence += pattern_score

        # 6. ML FEATURES
        if "ml_analyzer" in globals():
            regime = ml_analyzer.detect_market_regime(df)
            if regime == 2:
                confidence -= 15
                reasons.append("High Volatility ⚠️")

            rf_score = ml_analyzer.rf_signal_confirmation(df)
            if abs(rf_score) > 20:
                confidence += rf_score / 10
                reasons.append(f"ML Pattern Score: {rf_score}")

        # 7. NEWS SENTIMENT
        if "fetch_market_news" in globals():
            news_items = fetch_market_news(symbol, asset_type=asset_type)
            news_score, news_summary = analyze_news_sentiment(symbol, news_items)
            if news_score != 0:
                sentiment = "Bullish" if news_score > 0 else "Bearish"
                reasons.append(f"News: {sentiment}")
                if (base_action == "BUY" and news_score < 0) or (
                    base_action == "SELL" and news_score > 0
                ):
                    confidence -= 15

        # --- F. FINAL DECISION ---
        confidence = max(10.0, min(99.9, confidence))

        if confidence < 50 or base_action == "HOLD":
            return {
                "Symbol": symbol,
                "Action": "HOLD",
                "Reason": (
                    f"Low Confidence ({confidence:.1f}%)"
                    if base_action != "HOLD"
                    else "AI Hold"
                ),
            }

        # --- G. MONEY MANAGEMENT & ORDER ---
        current_price = last_row["Close"]
        atr = last_row.get("ATR_14", current_price * 0.01)

        sl_mult = 1.5 if asset_type == "forex" else 2.0
        sl_pips = atr * sl_mult
        tp_pips = sl_pips * 2.0

        entry_price = current_price
        order_type = "MARKET"

        # Pullback Logic for Forex
        ema_20 = last_row.get("SMA_20", current_price)
        dist_to_ema = abs(current_price - ema_20)

        if asset_type == "forex" and dist_to_ema > (atr * 0.8):
            order_type = "LIMIT"
            entry_price = (current_price + ema_20) / 2
            reasons.append("Pullback Entry")

        if base_action == "BUY":
            sl = entry_price - sl_pips
            tp = entry_price + tp_pips
            final_action = f"BUY {order_type}" if order_type == "LIMIT" else "BUY"
        else:
            sl = entry_price + sl_pips
            tp = entry_price - tp_pips
            final_action = f"SELL {order_type}" if order_type == "LIMIT" else "SELL"

        # Money Management (Kelly)
        user_balance = 1000
        if custom_balance:
            user_balance = custom_balance.get(
                "stock" if asset_type == "stock_indo" else "forex", 1000
            )

        sl_dist = abs(entry_price - sl)
        win_prob = confidence / 100.0

        # Gunakan Kelly Lot
        lot_size, mm_note = calculate_kelly_lot(
            user_balance, win_prob, 2.0, sl_dist, info
        )
        reasons.append(f"MM: {mm_note}")

        decimals = 0 if asset_type == "stock_indo" else 5

        return {
            "Symbol": symbol,
            "Action": final_action,
            "Price": round(entry_price, decimals),
            "Tp": round(tp, decimals),
            "Sl": round(sl, decimals),
            "LotSize": f"{lot_size} Lot",
            "LotNum": lot_size,
            "Prob": f"{confidence:.1f}%",
            "AI_Analysis": " | ".join(reasons),
        }

    except Exception as e:
        return {"error": f"Agent Error: {str(e)}"}
