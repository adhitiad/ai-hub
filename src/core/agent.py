import asyncio
import glob
import os

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from stable_baselines3 import PPO

# --- 2. ADVANCED ANALYSIS ---
from src.core.bandarmology import analyze_bandar_flow

# --- 1. DATA & ASSETS ---
from src.core.config_assets import get_asset_info
from src.core.data_loader import fetch_data_async  # [UPDATE] Async Loader

# IMPORT BARU: Gunakan logic fitur terpusat
from src.core.feature_enginering import enrich_data, get_model_input
from src.core.logger import logger
from src.core.market_structure import check_mtf_trend, detect_insider_volume
from src.core.model_loader import ModelCache
from src.core.money_management import calculate_kelly_lot, check_correlation_risk
from src.core.pattern_recognizer import detect_chart_patterns

# --- 3. RISK & MONEY MANAGEMENT ---
from src.core.risk_manager import risk_manager
from src.core.scoring import calculate_technical_score
from src.core.smart_money import analyze_smart_money
from src.core.vector_db import recall_similar_events
from src.core.whale_crypto import analyze_crypto_whales  # [UPDATE] Whale Detector

# --- 4. OPTIONAL MODULES (ML & News) ---
try:
    from src.core.ml_features import ml_analyzer
    from src.core.news_collector import analyze_news_sentiment, fetch_market_news
except ImportError:
    pass

MODEL_DIR = "models"


async def get_detailed_signal(symbol, asset_info=None, custom_balance=None):
    """
    ULTIMATE SIGNAL GENERATOR (Async Version + Crypto Support + Advanced Analysis + Stock Indo Support)
    """

    try:
        # --- A. SETUP & VALIDATION ---
        if not asset_info:
            info = get_asset_info(symbol)
            if not info:
                # Fallback jika config tidak ditemukan
                info = {
                    "symbol": symbol,
                    "type": (
                        "crypto"
                        if "/" in symbol
                        else "forex" if ".JK" in symbol else "stock_indo"
                    ),
                }
        else:
            info = asset_info

        # Deteksi Tipe Aset
        asset_type = info.get("type", "forex")
        category = info.get("category", "forex").lower()
        # overide stock indo mengandung ".JK"
        is_stock_indo = asset_type == "stock_indo" and ".JK" in symbol
        if is_stock_indo:
            asset_type = "stock_indo"
            category = "stock_indo"

        # Override jika simbol mengandung '/' (Ciri khas Crypto di CCXT)
        is_crypto = asset_type == "crypto" or "/" in symbol
        if is_crypto:
            asset_type = "crypto"
            category = "crypto"

        safe_symbol = symbol.replace("=", "").replace("^", "").replace("/", "")

        # --- B. GLOBAL RISK CHECKS ---
        # Pastikan fungsi-fungsi risk manager ini async atau dipanggil dengan benar
        can_trade, reject_reason = (
            await risk_manager.can_trade()
        )  # Panggil method public wrapper
        if not can_trade:
            return {
                "Symbol": symbol,
                "Action": "HOLD",
                "Reason": f"Risk: {reject_reason}",
            }

        is_uncorrelated, corr_msg = await check_correlation_risk(symbol)
        if not is_uncorrelated:
            return {"Symbol": symbol, "Action": "HOLD", "Reason": f"Risk: {corr_msg}"}

        # --- C. FETCH DATA (ASYNC) ---
        # Menggunakan loader baru yang support CCXT & YFinance secara async
        df = await fetch_data_async(symbol, period="2y", interval="1h")

        if df.empty:
            return {"Symbol": symbol, "Action": "HOLD", "Reason": "No Data Fetched"}

        # --- C. DATA ENRICHMENT ---
        df = enrich_data(df)

        # --- D. LOAD MODEL ---
        # Mencari model yang sesuai kategori (forex/stock/crypto)
        model = await ModelCache.get_model(symbol, category)

        # --- E. AI PREDICTION ---
        # --- E. AI PREDICTION (PERBAIKAN TOTAL) ---
        base_action = "HOLD"
        confidence = 50.0  # Start neutral

        if model:
            # 1. FILTER KOLOM: Hanya ambil kolom fitur yang dipelajari model
            df_features = get_model_input(df)

            # 2. NORMALISASI: Scaling data agar range-nya sama dengan saat training
            # Kita fit scaler pada seluruh history 2y agar distribusi nilainya valid
            scaler = StandardScaler()
            scaled_features = scaler.fit_transform(df_features)

            # 3. Ambil baris terakhir yang sudah ternormalisasi
            last_obs_features = scaled_features[-1]

            # 4. Tambahkan info posisi (0 = No Position)
            # Shape akhir harus match dengan env.observation_space
            obs = np.append(last_obs_features, [0]).astype(np.float32)

            # 5. Predict
            action, _ = await asyncio.to_thread(model.predict, obs)
            action_map = {0: "HOLD", 1: "BUY", 2: "SELL"}
            base_action = action_map[int(action)]

            # Base confidence dari AI
            if base_action != "HOLD":
                confidence = 65.0

        last_row = df.iloc[-1].copy()
        reasons = []

        # --- F. ADVANCED ANALYSIS INTEGRATION ---

        # 1. VECTOR DB RECALL (History Check)
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

        # 3. SPECIALIZED FLOW ANALYSIS (BANDAR vs WHALE)
        whale_data_info = None

        if is_crypto:
            # --- LOGIKA PAUS CRYPTO ---
            whale_data = await analyze_crypto_whales(symbol)
            whale_data_info = whale_data

            w_action = whale_data.get("action")
            w_score = whale_data.get("score", 0)

            if w_action == "BUY":
                reasons.append(whale_data["reason"])
                if base_action == "BUY":
                    confidence += 15
                elif base_action == "SELL":
                    confidence -= 25
            elif w_action == "SELL":
                reasons.append(whale_data["reason"])
                if base_action == "SELL":
                    confidence += 15
                elif base_action == "BUY":
                    confidence -= 25

            # Ekstra Logika berdasarkan Score
            if w_score > 20 and base_action == "SELL":
                confidence += 10
                reasons.append("Whale Activity confirms SELL 📉")
            elif w_score < -20 and base_action == "BUY":
                confidence += 10
                reasons.append("Whale Activity confirms BUY 📈")

        elif asset_type == "stock_indo":
            # --- LOGIKA BANDARMOLOGY SAHAM ---
            bandar_result = analyze_bandar_flow(df)
            flow_status = bandar_result["status"]
            if base_action == "BUY" and "ACCUM" in flow_status:
                confidence += 15
                reasons.append("Bandar Accumulation 💰")
            elif base_action == "SELL" and "DISTRIB" in flow_status:
                confidence += 15
                reasons.append("Bandar Distribution 📉")

        # 4. INSIDER VOLUME (Umum)
        if detect_insider_volume(df):
            confidence += 10
            reasons.append("Insider Volume Spike 🐳")

        # 5. CHART PATTERNS
        pattern_score, detected_patterns = detect_chart_patterns(df)
        if detected_patterns:
            reasons.append(f"Patterns: {', '.join(detected_patterns)}")
            confidence += pattern_score

        # 6. ML FEATURES (Random Forest)
        if "ml_analyzer" in globals():
            # rf_signal_confirmation sudah otomatis handle enrich & input shape
            rf_score = ml_analyzer.rf_signal_confirmation(df)

            if abs(rf_score) > 20:
                confidence += rf_score / 10
                reasons.append(f"RF Model: {rf_score}")

                # Logic override jika RF sangat yakin tapi PPO ragu
                if rf_score > 80 and base_action == "HOLD":
                    base_action = "BUY"
                    reasons.append("RF Strong Override")
                elif rf_score < -80 and base_action == "HOLD":
                    base_action = "SELL"
                    reasons.append("RF Strong Override")

        # 7. NEWS SENTIMENT
        if "fetch_market_news" in globals():
            news_items = await asyncio.to_thread(
                fetch_market_news, symbol, asset_type=asset_type
            )
            news_score, news_summary = analyze_news_sentiment(symbol, news_items)
            if news_score != 0:
                sentiment = "Bullish" if news_score > 0 else "Bearish"
                reasons.append(f"News: {sentiment}")
                if (base_action == "BUY" and news_score < 0) or (
                    base_action == "SELL" and news_score > 0
                ):
                    confidence -= 15

        # --- G. FINAL DECISION ---
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

        # --- H. MONEY MANAGEMENT & ORDER ---
        current_price = last_row["Close"]
        atr = last_row.get("ATR_14", current_price * 0.01)

        # Dynamic Risk Multiplier
        sl_mult = 2.0  # Default Stock
        if asset_type == "forex":
            sl_mult = 1.5
        elif asset_type == "crypto":
            sl_mult = 3.0  # Crypto lebih volatile

        sl_pips = atr * sl_mult
        tp_pips = sl_pips * 2.0  # Risk Reward 1:2

        entry_price = current_price
        order_type = "MARKET"

        # Pullback Logic
        ema_20 = last_row.get("SMA_20", current_price)
        dist_to_ema = abs(current_price - ema_20)

        if dist_to_ema > (atr * 0.8):
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

        # Hitung Lot Size (Kelly Criterion)
        user_balance = 1000
        if custom_balance:
            if asset_type == "crypto":
                user_balance = custom_balance.get("crypto", 1000)
            elif asset_type == "stock_indo":
                user_balance = custom_balance.get("stock", 1000)
            else:
                user_balance = custom_balance.get("forex", 1000)

        sl_dist = abs(entry_price - sl)
        win_prob = confidence / 100.0

        lot_size, mm_note = calculate_kelly_lot(
            user_balance, win_prob, 2.0, sl_dist, info
        )
        reasons.append(f"MM: {mm_note}")

        # Formatting Output
        decimals = 0 if asset_type == "stock_indo" else 5
        if asset_type == "crypto":
            decimals = 2 if current_price > 1 else 6

        result = {
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

        # Tambahkan Info Whale khusus Crypto untuk Debug/UI
        if is_crypto and whale_data_info:
            result["Whale_Activity"] = (
                f"{whale_data_info.get('score', 0):.1f}% ({whale_data_info.get('action')})"
            )

        return result

    except Exception as e:
        return {"error": f"Agent Error ({symbol}): {str(e)}"}


# Test Runner (Optional)
def test_agent():
    # Test cases can be added here
    pass
    pass
